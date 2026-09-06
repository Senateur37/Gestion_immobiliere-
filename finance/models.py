"""Modeles du domaine financier.

Le modele d'origine confondait trois faits distincts dans une seule
table : ce qui est du, ce qui a ete verse, et ce que ce versement solde.
D'ou l'impossibilite de representer un paiement partiel, une avance, ou
un versement couvrant deux mois.

    RentCharge   ce que le locataire doit, pour une periode donnee
    Payment      ce qu'il a effectivement verse, en une fois
    Allocation   la part d'un versement imputee sur une echeance

Un versement peut ainsi solder plusieurs echeances, et une echeance etre
soldee par plusieurs versements.
"""
from decimal import Decimal

from django.db import models

from core.models import TenantOwnedModel


class RentCharge(TenantOwnedModel):
    """Somme due par un locataire pour une periode.

    Le statut n'est jamais saisi a la main : il decoule des imputations
    recues.
    """

    STATUS_PENDING = 'pending'
    STATUS_PARTIAL = 'partial'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'A payer'),
        (STATUS_PARTIAL, 'Partiellement payee'),
        (STATUS_PAID, 'Payee'),
        (STATUS_CANCELLED, 'Annulee'),
    ]

    KIND_CHOICES = [
        ('rent', 'Loyer'),
        ('charges', 'Charges'),
        ('deposit', 'Depot de garantie'),
        ('fee', 'Frais'),
        ('other', 'Autre'),
    ]

    lease = models.ForeignKey(
        'Locations.Lease',
        on_delete=models.CASCADE,
        related_name='rent_charges',
        verbose_name="Bail",
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='rent', verbose_name="Nature")
    label = models.CharField(max_length=200, blank=True, verbose_name="Libelle")

    period_start = models.DateField(verbose_name="Debut de periode")
    period_end = models.DateField(verbose_name="Fin de periode")
    due_date = models.DateField(verbose_name="Echeance")

    amount_due = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant du")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="Statut"
    )

    class Meta:
        db_table = 'finance_rentcharge'
        ordering = ['due_date']
        # Une periode ne peut etre facturee deux fois pour la meme nature.
        # C'est ce qui rend la generation d'echeancier rejouable sans
        # produire de doublons.
        unique_together = [['lease', 'kind', 'period_start']]
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['lease', 'due_date']),
            models.Index(fields=['due_date', 'status']),
        ]
        verbose_name = "Echeance"
        verbose_name_plural = "Echeances"

    def __str__(self):
        return f'{self.get_kind_display()} du {self.period_start} : {self.amount_due}'

    @property
    def amount_allocated(self):
        """Total effectivement impute sur cette echeance."""
        total = self.allocations.aggregate(total=models.Sum('amount'))['total']
        return total or Decimal('0')

    @property
    def amount_outstanding(self):
        """Reste a payer. Jamais negatif : un trop-percu n'est pas une dette."""
        reste = self.amount_due - self.amount_allocated
        return reste if reste > 0 else Decimal('0')

    @property
    def is_settled(self):
        return self.amount_allocated >= self.amount_due

    def is_overdue(self, today):
        """En retard : echeance depassee et solde non nul."""
        return (
            self.status != self.STATUS_CANCELLED
            and self.amount_outstanding > 0
            and self.due_date < today
        )


class Payment(TenantOwnedModel):
    """Somme effectivement recue.

    Un versement existe independamment de ce qu'il solde : c'est ce qui
    permet d'enregistrer une avance, puis de l'imputer plus tard.
    """

    METHOD_CASH = 'cash'
    METHOD_BANK = 'bank_transfer'
    METHOD_CHECK = 'check'
    METHOD_CARD = 'card'
    METHOD_ORANGE_MONEY = 'orange_money'
    METHOD_MOOV_MONEY = 'moov_money'

    METHOD_CHOICES = [
        (METHOD_CASH, 'Especes'),
        (METHOD_BANK, 'Virement bancaire'),
        (METHOD_CHECK, 'Cheque'),
        (METHOD_CARD, 'Carte bancaire'),
        (METHOD_ORANGE_MONEY, 'Orange Money'),
        (METHOD_MOOV_MONEY, 'Moov Money'),
    ]

    lease = models.ForeignKey(
        'Locations.Lease',
        on_delete=models.PROTECT,
        related_name='finance_payments',
        verbose_name="Bail",
    )
    reference = models.CharField(max_length=50, verbose_name="Reference")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant recu")
    payment_date = models.DateField(verbose_name="Date de paiement")
    method = models.CharField(max_length=30, choices=METHOD_CHOICES, verbose_name="Mode de paiement")

    # Reference de l'operateur pour un paiement mobile ou un virement :
    # indispensable au rapprochement.
    external_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Reference externe",
        help_text="Numero de transaction Orange Money ou Moov Money, avis de virement.",
    )
    # Tout encaissement entre dans un compte financier reel : sans cela,
    # l'argent est enregistre nulle part et la tresorerie ne reflete plus
    # la realite. Le compte determine aussi le compte comptable mouvemente.
    compte = models.ForeignKey(
        'comptes.Compte',
        on_delete=models.PROTECT,
        related_name='encaissements_loyers',
        verbose_name="Compte encaisseur",
        help_text="Caisse, banque ou compte mobile ou la somme a ete versee.",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        db_table = 'finance_payment'
        ordering = ['-payment_date', '-created_at']
        unique_together = [['organization', 'reference']]
        indexes = [
            models.Index(fields=['organization', 'payment_date']),
            models.Index(fields=['lease', 'payment_date']),
        ]
        verbose_name = "Encaissement"
        verbose_name_plural = "Encaissements"

    def __str__(self):
        return f'{self.reference} : {self.amount}'

    @property
    def amount_allocated(self):
        total = self.allocations.aggregate(total=models.Sum('amount'))['total']
        return total or Decimal('0')

    @property
    def amount_unallocated(self):
        """Part non encore imputee : une avance, en pratique."""
        return self.amount - self.amount_allocated


class PaymentAllocation(TenantOwnedModel):
    """Part d'un encaissement imputee sur une echeance.

    C'est cette table qui manquait. Sans elle, un versement de 60 000 sur
    un loyer de 100 000 ne pouvait etre represente qu'en denaturant l'un
    ou l'autre.
    """

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='allocations', verbose_name="Encaissement"
    )
    rent_charge = models.ForeignKey(
        RentCharge, on_delete=models.CASCADE, related_name='allocations', verbose_name="Echeance"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant impute")

    class Meta:
        db_table = 'finance_paymentallocation'
        ordering = ['-created_at']
        # Un encaissement ne s'impute qu'une fois sur une meme echeance :
        # deux imputations partielles se cumulent en une seule ligne.
        unique_together = [['payment', 'rent_charge']]
        indexes = [
            models.Index(fields=['organization', 'created_at']),
        ]
        verbose_name = "Imputation"
        verbose_name_plural = "Imputations"

    def __str__(self):
        return f'{self.amount} de {self.payment.reference}'
