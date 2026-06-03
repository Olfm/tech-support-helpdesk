# Сигналы: шлю уведомления, когда у заявки меняется статус
# или когда в переписке появляется новое сообщение.

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Notification, Ticket, TicketComment


@receiver(pre_save, sender=Ticket)
def remember_previous_status(sender, instance, **kwargs):
    # перед сохранением запоминаю старый статус, чтобы потом понять, поменялся ли он
    if instance.pk:
        previous = sender.objects.filter(pk=instance.pk).only("status").first()
        instance._previous_status = previous.status if previous else None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Ticket)
def notify_author_on_status_change(sender, instance, created, **kwargs):
    # если статус сменился, говорю об этом автору заявки
    if created:
        return
    previous = getattr(instance, "_previous_status", None)
    if previous is not None and previous != instance.status:
        Notification.objects.create(
            recipient=instance.author,
            ticket=instance,
            message=(
                f"Статус заявки #{instance.pk} изменён на "
                f"«{instance.get_status_display()}»"
            ),
        )


@receiver(post_save, sender=TicketComment)
def notify_on_new_comment(sender, instance, created, **kwargs):
    # на новое сообщение уведомляю вторую сторону переписки
    if not created:
        return
    ticket = instance.ticket
    # если написал автор, шлём оператору, и наоборот
    if instance.author_id == ticket.author_id:
        recipient = ticket.assignee
    else:
        recipient = ticket.author
    if recipient and recipient != instance.author:
        Notification.objects.create(
            recipient=recipient,
            ticket=ticket,
            message=f"Новый ответ по заявке #{ticket.pk}: {ticket.title}",
        )
