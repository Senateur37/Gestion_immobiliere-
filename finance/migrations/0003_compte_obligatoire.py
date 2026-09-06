"""Le compte encaisseur devient obligatoire.

Un encaissement sans compte n'entre dans aucune tresorerie et ne produit
aucune ecriture : l'argent est enregistre nulle part. Le champ etait
facultatif le temps de l'integration ; il ne peut plus l'etre.

Les encaissements anterieurs sont rattaches au premier compte de caisse
disponible. Attention : ce rattachement ne cree ni mouvement de
tresorerie ni ecriture comptable — une migration n'a pas a inventer des
operations financieres. La regularisation de ces lignes est une decision
metier, a mener separement.
"""
from django.db import migrations, models
import django.db.models.deletion


def rattacher_les_encaissements_orphelins(apps, schema_editor):
    Payment = apps.get_model('finance', 'Payment')
    Compte = apps.get_model('comptes', 'Compte')

    orphelins = Payment.objects.filter(compte__isnull=True)
    if not orphelins.exists():
        return

    compte = Compte.objects.filter(type='CAISSE', actif=True).order_by('pk').first()
    if compte is None:
        compte = Compte.objects.order_by('pk').first()
    if compte is None:
        raise RuntimeError(
            "Des encaissements sont sans compte et aucun compte financier "
            "n'existe. Creez au moins une caisse avant d'appliquer cette "
            "migration."
        )

    orphelins.update(compte=compte)


def revenir_en_arriere(apps, schema_editor):
    """Rien a defaire : la colonne redevient simplement facultative."""


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_payment_compte'),
        ('comptes', '0005_compte_entreprise_id_alter_compte_code_and_more'),
    ]

    operations = [
        migrations.RunPython(rattacher_les_encaissements_orphelins, revenir_en_arriere),
        migrations.AlterField(
            model_name='payment',
            name='compte',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='encaissements_loyers',
                to='comptes.compte',
                verbose_name='Compte encaisseur',
                help_text='Caisse, banque ou compte mobile ou la somme a ete versee.',
            ),
        ),
    ]
