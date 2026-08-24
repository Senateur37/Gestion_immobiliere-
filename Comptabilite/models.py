from django.conf import settings
from django.db import models


class Transaction(models.Model):
	"""Mouvement financier rattachable a un utilisateur ou un bail."""
	TYPE_CHOICES = [
		('income', 'Recette'),
		('expense', 'Depense'),
	]

	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
	transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
	label = models.CharField(max_length=200)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	transaction_date = models.DateField()
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-transaction_date', '-created_at']
		indexes = [models.Index(fields=['owner', 'transaction_date'])]

	def __str__(self):
		return f'{self.label} - {self.amount}'
