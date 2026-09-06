"""Vues de l'API v1.

Chaque vue valide une entree, appelle un service, et serialise le
resultat. Aucune ne manipule les modeles pour ecrire : les regles metier
restent dans les services, communes a l'API et aux ecrans Django.

Le perimetre vient de la permission IsOrganizationMember, qui installe
l'organisation active. Les managers filtrent ensuite d'office : une vue
qui oublierait de restreindre ne fuiterait pas.
"""
from datetime import date

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import DomainError
from core.permissions import HasOrganizationRole, IsOrganizationMember
from finance.models import Payment, RentCharge
from finance.services import generate_rent_schedule, record_payment
from Locations.models import Lease
from organizations.models import Membership
from Proprietes.models import Property, Unit
from Proprietes.services import create_property, create_unit, portfolio_summary

from .serializers import (
    CompteSerializer,
    DocumentSerializer,
    EcritureSerializer,
    LeaseSerializer,
    LocataireSerializer,
    MaintenanceSerializer,
    MembreSerializer,
    PaymentSerializer,
    PropertySerializer,
    RecordPaymentSerializer,
    RentChargeSerializer,
    UnitSerializer,
)


class PropertyListCreateView(APIView):
    """GET liste les biens, POST en cree un."""

    permission_classes = [IsOrganizationMember]

    def get(self, request):
        biens = Property.objects.prefetch_related('units')
        recherche = request.query_params.get('q', '').strip()
        if recherche:
            biens = biens.filter(name__icontains=recherche) | biens.filter(city__icontains=recherche)
        return Response(PropertySerializer(biens, many=True).data)

    def post(self, request):
        entree = PropertySerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        try:
            bien = create_property(owner=request.user, **entree.validated_data)
        except DomainError as erreur:
            return Response({'detail': erreur.message, 'code': erreur.code}, status=400)
        return Response(PropertySerializer(bien).data, status=status.HTTP_201_CREATED)


class PropertyDetailView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request, pk):
        try:
            bien = Property.objects.prefetch_related('units').get(pk=pk)
        except Property.DoesNotExist:
            return Response({'detail': 'Bien introuvable.'}, status=404)
        return Response(PropertySerializer(bien).data)


class UnitListCreateView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request):
        unites = Unit.objects.select_related('property')
        bien = request.query_params.get('property')
        if bien:
            unites = unites.filter(property_id=bien)
        statut = request.query_params.get('status')
        if statut:
            unites = unites.filter(status=statut)
        return Response(UnitSerializer(unites, many=True).data)

    def post(self, request):
        entree = UnitSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = dict(entree.validated_data)
        identifiant_bien = donnees.pop('property_id')
        try:
            # Resolu par le manager filtre : impossible de rattacher une
            # unite au bien d'une autre organisation.
            bien = Property.objects.get(pk=identifiant_bien)
        except Property.DoesNotExist:
            return Response({'detail': 'Bien introuvable.', 'code': 'property_not_found'}, status=404)

        try:
            unite = create_unit(property=bien, **donnees)
        except DomainError as erreur:
            return Response({'detail': erreur.message, 'code': erreur.code}, status=400)
        return Response(UnitSerializer(unite).data, status=status.HTTP_201_CREATED)


class LeaseListView(ListAPIView):
    permission_classes = [IsOrganizationMember]
    serializer_class = LeaseSerializer
    pagination_class = None

    def get_queryset(self):
        baux = Lease.objects.select_related('unit', 'unit__property', 'tenant')
        statut = self.request.query_params.get('status')
        if statut:
            baux = baux.filter(status=statut)
        return baux


class RentChargeListView(ListAPIView):
    """Echeances : ce que les locataires doivent."""

    permission_classes = [IsOrganizationMember]
    serializer_class = RentChargeSerializer
    pagination_class = None

    def get_queryset(self):
        charges = RentCharge.objects.select_related(
            'lease', 'lease__unit', 'lease__unit__property', 'lease__tenant'
        )
        statut = self.request.query_params.get('status')
        if statut == 'overdue':
            charges = charges.filter(due_date__lt=date.today()).exclude(
                status__in=[RentCharge.STATUS_PAID, RentCharge.STATUS_CANCELLED]
            )
        elif statut:
            charges = charges.filter(status=statut)
        return charges


class PaymentListView(ListAPIView):
    """Encaissements : ce qui a effectivement ete recu."""

    permission_classes = [IsOrganizationMember]
    serializer_class = PaymentSerializer
    pagination_class = None

    def get_queryset(self):
        return Payment.objects.select_related('lease', 'lease__tenant')


class RecordPaymentView(APIView):
    """POST enregistre un encaissement et l'impute automatiquement.

    Reserve aux roles habilites : un agent encaisse, un observateur non.
    """

    permission_classes = [HasOrganizationRole]
    required_role = Membership.ROLE_AGENT

    def post(self, request):
        entree = RecordPaymentSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        try:
            bail = Lease.objects.get(pk=donnees['lease'])
        except Lease.DoesNotExist:
            return Response({'detail': 'Bail introuvable.', 'code': 'lease_not_found'}, status=404)

        from comptes.models import Compte

        try:
            compte = Compte.objects.get(pk=donnees['compte'])
        except Compte.DoesNotExist:
            return Response({'detail': 'Compte introuvable.', 'code': 'compte_not_found'}, status=404)

        try:
            paiement = record_payment(
                lease=bail,
                amount=donnees['amount'],
                payment_date=donnees['payment_date'],
                method=donnees['method'],
                external_reference=donnees.get('external_reference', ''),
                notes=donnees.get('notes', ''),
                compte=compte,
                user=request.user,
            )
        except DomainError as erreur:
            return Response({'detail': erreur.message, 'code': erreur.code}, status=400)

        return Response(PaymentSerializer(paiement).data, status=status.HTTP_201_CREATED)


class GenerateScheduleView(APIView):
    """POST produit l'echeancier d'un bail."""

    permission_classes = [HasOrganizationRole]
    required_role = Membership.ROLE_MANAGER

    def post(self, request, pk):
        try:
            bail = Lease.objects.get(pk=pk)
        except Lease.DoesNotExist:
            return Response({'detail': 'Bail introuvable.'}, status=404)

        try:
            creees = generate_rent_schedule(lease=bail)
        except DomainError as erreur:
            return Response({'detail': erreur.message, 'code': erreur.code}, status=400)

        return Response({'created': len(creees)}, status=status.HTTP_201_CREATED)


class ComptesListView(APIView):
    """Comptes financiers disponibles pour un encaissement."""

    permission_classes = [IsOrganizationMember]

    def get(self, request):
        from comptes.models import Compte

        return Response(CompteSerializer(Compte.objects.filter(actif=True), many=True).data)


@api_view(['GET'])
@permission_classes([IsOrganizationMember])
def dashboard(request):
    """Chiffres d'ouverture, en une requete.

    Le front n'a pas a enchainer cinq appels pour afficher son ecran
    d'accueil.
    """
    patrimoine = portfolio_summary()

    charges_ouvertes = RentCharge.objects.exclude(
        status__in=[RentCharge.STATUS_PAID, RentCharge.STATUS_CANCELLED]
    )
    aujourdhui = date.today()
    en_retard = charges_ouvertes.filter(due_date__lt=aujourdhui)

    # Le reste a payer se calcule echeance par echeance : une somme SQL
    # ignorerait les versements deja imputes.
    reste = sum((charge.amount_outstanding for charge in charges_ouvertes), start=0)
    reste_en_retard = sum((charge.amount_outstanding for charge in en_retard), start=0)

    return Response({
        'organization': {
            'name': request.organization.name,
            'currency': request.organization.currency,
        },
        'portfolio': patrimoine,
        'leases': {
            'active': Lease.objects.filter(status='active').count(),
            'total': Lease.objects.count(),
        },
        'finance': {
            'open_charges': charges_ouvertes.count(),
            'outstanding': reste,
            'overdue_charges': en_retard.count(),
            'overdue_amount': reste_en_retard,
            'collected': Payment.objects.aggregate(total=Sum('amount'))['total'] or 0,
        },
    })


# ---------------------------------------------------------------------------
# Ecrans repris de l'interface Django
# ---------------------------------------------------------------------------

class LocataireListView(APIView):
    """Locataires de l'organisation, avec leur solde.

    Le perimetre vient des baux : on ne liste pas les comptes de la
    plateforme, mais les personnes reellement liees a l'organisation.
    """

    permission_classes = [IsOrganizationMember]

    def get(self, request):
        from django.contrib.auth import get_user_model

        from finance.services import lease_balance

        Utilisateur = get_user_model()
        baux = Lease.objects.select_related('tenant')

        identifiants = set(baux.values_list('tenant_id', flat=True))
        locataires = Utilisateur.objects.filter(pk__in=identifiants)

        # Un locataire peut avoir plusieurs baux : on retient le plus
        # recent actif pour l'affichage, et on cumule les soldes.
        par_locataire = {}
        for bail in baux.order_by('-start_date'):
            entree = par_locataire.setdefault(bail.tenant_id, {'baux': [], 'actif': None})
            entree['baux'].append(bail)
            if entree['actif'] is None and bail.status == 'active':
                entree['actif'] = bail

        resultat = []
        for personne in locataires:
            entree = par_locataire.get(personne.pk, {'baux': [], 'actif': None})
            personne.leases_count = len(entree['baux'])
            personne.bail_actif = entree['actif']
            personne.balance = sum((lease_balance(b) for b in entree['baux']), start=0)
            resultat.append(personne)

        return Response(LocataireSerializer(resultat, many=True).data)


class MaintenanceListView(ListAPIView):
    permission_classes = [IsOrganizationMember]
    serializer_class = MaintenanceSerializer
    pagination_class = None

    def get_queryset(self):
        from Maintenance.models import MaintenanceRequest

        # MaintenanceRequest n'est pas encore rattache a l'organisation :
        # il s'y raccroche par l'unite, qui l'est. Ce relais disparaitra
        # quand le domaine sera migre.
        demandes = MaintenanceRequest.objects.filter(
            unit__in=Unit.objects.all()
        ).select_related('unit', 'unit__property')

        statut = self.request.query_params.get('status')
        if statut:
            demandes = demandes.filter(status=statut)
        return demandes


class DocumentListView(ListAPIView):
    permission_classes = [IsOrganizationMember]
    serializer_class = DocumentSerializer
    pagination_class = None

    def get_queryset(self):
        from Documents.models import Document

        # Document porte encore son propre owner, faute d'avoir ete migre.
        documents = Document.objects.filter(owner=self.request.user)
        categorie = self.request.query_params.get('category')
        if categorie:
            documents = documents.filter(category=categorie)
        return documents


class EcritureListView(APIView):
    """Journal comptable de l'organisation."""

    permission_classes = [HasOrganizationRole]
    required_role = Membership.ROLE_ACCOUNTANT

    def get(self, request):
        from comptabilite_ohada.models import EcritureComptable
        from organizations.entreprise import entreprise_id_courant

        ecritures = EcritureComptable.objects.select_related('journal').prefetch_related(
            'lignes__compte'
        )
        # La comptabilite n'est pas filtree par un manager : on applique
        # ici le perimetre, faute de quoi une organisation verrait les
        # ecritures des autres.
        identifiant = entreprise_id_courant()
        if identifiant:
            ecritures = ecritures.filter(entreprise_id=identifiant)

        ecritures = ecritures.order_by('-date_ecriture', '-id')[:200]
        return Response(EcritureSerializer(ecritures, many=True).data)


class MembreListView(ListAPIView):
    """Membres de l'organisation active."""

    permission_classes = [HasOrganizationRole]
    required_role = Membership.ROLE_MANAGER
    serializer_class = MembreSerializer
    pagination_class = None

    def get_queryset(self):
        return Membership.objects.filter(
            organization=self.request.organization
        ).select_related('user')


@api_view(['GET'])
@permission_classes([IsOrganizationMember])
def rapport(request):
    """Chiffres de synthese, plus detailles que le tableau de bord."""
    from comptes.models import Compte
    from Maintenance.models import MaintenanceRequest

    unites = Unit.objects.all()
    baux_actifs = Lease.objects.filter(status='active')
    charges = RentCharge.objects.exclude(
        status__in=[RentCharge.STATUS_PAID, RentCharge.STATUS_CANCELLED]
    )

    loyer_total = baux_actifs.aggregate(total=Sum('rent_amount'))['total'] or 0
    nombre_baux = baux_actifs.count()

    repartition = {}
    for valeur, libelle in Unit.STATUS_CHOICES:
        repartition[libelle] = unites.filter(status=valeur).count()

    etat_charges = {}
    for valeur, libelle in RentCharge.STATUS_CHOICES:
        etat_charges[libelle] = RentCharge.objects.filter(status=valeur).count()

    return Response({
        'rent': {
            'monthly_total': loyer_total,
            'average': round(loyer_total / nombre_baux) if nombre_baux else 0,
            'active_leases': nombre_baux,
        },
        'units_by_status': repartition,
        'charges_by_status': etat_charges,
        'outstanding': sum((charge.amount_outstanding for charge in charges), start=0),
        'collected': Payment.objects.aggregate(total=Sum('amount'))['total'] or 0,
        'maintenance_open': MaintenanceRequest.objects.filter(
            unit__in=unites, status__in=['submitted', 'in_progress']
        ).count(),
        'treasury': [
            {'code': c.code, 'nom': c.nom, 'solde': c.solde_actuel}
            for c in Compte.objects.filter(actif=True)
        ],
    })
