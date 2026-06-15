from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.roles import is_operator
from .forms import TicketCommentForm, TicketForm, TicketManageForm
from .models import Category, Notification, Ticket
from .services import auto_assign_ticket


def home(request):
    # главная страница, открыта всем
    return render(request, "tickets/home.html")


@login_required
def dashboard(request):
    # личный кабинет. Оператору показываю очередь и сводку, обычному юзеру - его заявки
    if is_operator(request.user):
        open_tickets = Ticket.objects.filter(status__in=Ticket.OPEN_STATUSES)
        context = {
            "is_operator": True,
            "total_open": open_tickets.count(),
            "unassigned": open_tickets.filter(assignee__isnull=True).count(),
            "my_queue": open_tickets.filter(assignee=request.user).select_related("category", "author"),
            "recent": Ticket.objects.select_related("category", "author")[:10],
        }
    else:
        tickets = request.user.tickets.select_related("category", "assignee")
        context = {
            "is_operator": False,
            "tickets": tickets,
            "open_count": tickets.filter(status__in=Ticket.OPEN_STATUSES).count(),
        }
    return render(request, "tickets/dashboard.html", context)


@login_required
def ticket_create(request):
    # подача новой заявки. После сохранения сразу гоню её через классификацию и назначение
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.author = request.user
            if not ticket.contact_email:
                ticket.contact_email = request.user.email
            ticket.save()
            auto_assign_ticket(ticket)
            messages.success(request, f"Заявка #{ticket.pk} создана.")
            return redirect(ticket.get_absolute_url())
    else:
        form = TicketForm()
    return render(request, "tickets/ticket_form.html", {"form": form})


@login_required
def ticket_list(request):
    # оператор видит все заявки (с фильтром по статусу), пользователь - только свои
    if is_operator(request.user):
        tickets = Ticket.objects.select_related("category", "author", "assignee")
        status = request.GET.get("status")
        if status in dict(Ticket.Status.choices):
            tickets = tickets.filter(status=status)
        if request.GET.get("mine") == "1":
            tickets = tickets.filter(assignee=request.user)
    else:
        tickets = request.user.tickets.select_related("category", "assignee")

    context = {
        "tickets": tickets,
        "is_operator": is_operator(request.user),
        "statuses": Ticket.Status.choices,
        "current_status": request.GET.get("status", ""),
    }
    return render(request, "tickets/ticket_list.html", context)


@login_required
def ticket_detail(request, pk):
    # карточка заявки: переписка и, если это оператор, управление статусом и исполнителем
    ticket = get_object_or_404(
        Ticket.objects.select_related("category", "author", "assignee"), pk=pk
    )

    operator = is_operator(request.user)
    # чужую заявку обычному пользователю смотреть нельзя
    if not operator and ticket.author_id != request.user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect("tickets:ticket_list")

    comment_form = TicketCommentForm()
    manage_form = TicketManageForm(instance=ticket) if operator else None

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "comment":
            # добавили сообщение в переписку
            comment_form = TicketCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.author = request.user
                comment.save()
                messages.success(request, "Сообщение добавлено.")
                return redirect(ticket.get_absolute_url())
        elif action == "manage" and operator:
            # оператор поменял статус/исполнителя/категорию
            manage_form = TicketManageForm(request.POST, instance=ticket)
            if manage_form.is_valid():
                updated = manage_form.save(commit=False)
                # если перевели в "решена" - ставим время, если убрали из "решена" - сбрасываем
                if updated.status == Ticket.Status.RESOLVED and updated.resolved_at is None:
                    updated.resolved_at = timezone.now()
                if updated.status != Ticket.Status.RESOLVED:
                    updated.resolved_at = None
                updated.save()
                messages.success(request, "Заявка обновлена.")
                return redirect(ticket.get_absolute_url())
        elif action == "resolve" and (operator or ticket.author_id == request.user.id):
            ticket.mark_resolved()
            messages.success(request, "Заявка отмечена как решённая.")
            return redirect(ticket.get_absolute_url())

    context = {
        "ticket": ticket,
        "comments": ticket.comments.select_related("author"),
        "comment_form": comment_form,
        "manage_form": manage_form,
        "is_operator": operator,
    }
    return render(request, "tickets/ticket_detail.html", context)


@login_required
@user_passes_test(is_operator)
def reports(request):
    # отчёты для операторов: сколько заявок по статусам и категориям, среднее время решения
    by_status = (
        Ticket.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    status_labels = dict(Ticket.Status.choices)
    by_status = [
        {"label": status_labels.get(row["status"], row["status"]), "count": row["count"]}
        for row in by_status
    ]

    by_category = (
        Ticket.objects.values(name=F("category__name"))
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    resolved = Ticket.objects.filter(resolved_at__isnull=False)
    avg_hours = None
    if resolved.exists():
        total = sum(t.resolution_hours() or 0 for t in resolved)
        avg_hours = round(total / resolved.count(), 1)

    context = {
        "total": Ticket.objects.count(),
        "open": Ticket.objects.filter(status__in=Ticket.OPEN_STATUSES).count(),
        "resolved_count": resolved.count(),
        "avg_resolution_hours": avg_hours,
        "by_status": by_status,
        "by_category": by_category,
    }
    return render(request, "tickets/reports.html", context)


@login_required
def notifications(request):
    # список уведомлений пользователя
    items = request.user.notifications.select_related("ticket")
    return render(request, "tickets/notifications.html", {"items": items})


@login_required
def notification_read(request, pk):
    # помечаю уведомление прочитанным и веду на связанную заявку
    note = get_object_or_404(Notification, pk=pk, recipient=request.user)
    note.is_read = True
    note.save(update_fields=["is_read"])
    if note.ticket_id:
        return redirect(note.ticket.get_absolute_url())
    return redirect("tickets:notifications")


@login_required
def notifications_read_all(request):
    # помечаю все уведомления прочитанными
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("tickets:notifications")
