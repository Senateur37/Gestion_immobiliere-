"""Rattachement des baux a une organisation.

L'organisation n'est pas devinee : elle est heritee de l'unite louee,
qui la porte depuis la migration de Proprietes. Un bail appartient
forcement a la meme organisation que son unite.
"""
from django.db import migrations, models
import django.db.models.deletion


def heriter_de_l_unite(apps, schema_editor):
    """Chaque bail, colocataire et etat des lieux suit l'unite concernee."""
    Lease = apps.get_model('Locations', 'Lease')
    LeaseTenant = apps.get_model('Locations', 'LeaseTenant')
    Inspection = apps.get_model('Locations', 'Inspection')

    for bail in Lease.objects.select_related('unit').iterator():
        bail.organization_id = bail.unit.organization_id
        bail.save(update_fields=['organization'])

    for colocataire in LeaseTenant.objects.select_related('lease').iterator():
        colocataire.organization_id = colocataire.lease.organization_id
        colocataire.save(update_fields=['organization'])

    for etat_des_lieux in Inspection.objects.select_related('lease').iterator():
        etat_des_lieux.organization_id = etat_des_lieux.lease.organization_id
        etat_des_lieux.save(update_fields=['organization'])


def revenir_en_arriere(apps, schema_editor):
    """Rien a defaire : la colonne disparait avec le retour en arriere."""


class Migration(migrations.Migration):

    dependencies = [
        ('Locations', '0002_alter_lease_created_at_alter_lease_deposit_amount_and_more'),
        ('Proprietes', '0004_alter_property_created_at_and_more'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        # 1. Colonnes facultatives.
        migrations.AddField(
            model_name='lease',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Locations_lease_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AddField(
            model_name='leasetenant',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Locations_leasetenant_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AddField(
            model_name='inspection',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Locations_inspection_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        # Horodatages apportes par TimeStampedModel.
        migrations.AddField(
            model_name='leasetenant',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Cree le'),
        ),
        migrations.AddField(
            model_name='leasetenant',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Mis a jour le'),
        ),
        migrations.AddField(
            model_name='inspection',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Mis a jour le'),
        ),

        # 2. Remplissage depuis l'unite.
        migrations.RunPython(heriter_de_l_unite, revenir_en_arriere),

        # 3. Colonnes obligatoires.
        migrations.AlterField(
            model_name='lease',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Locations_lease_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AlterField(
            model_name='leasetenant',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Locations_leasetenant_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AlterField(
            model_name='inspection',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Locations_inspection_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),

        # Le numero de bail n'est plus unique pour toute la base, mais a
        # l'interieur de chaque organisation.
        migrations.AlterField(
            model_name='lease',
            name='lease_number',
            field=models.CharField(max_length=50, verbose_name='Numero de bail'),
        ),
        migrations.AlterUniqueTogether(
            name='lease',
            unique_together={('organization', 'lease_number')},
        ),
        migrations.AddIndex(
            model_name='lease',
            index=models.Index(fields=['organization', 'status'], name='leases_leas_organiz_e0b1f2_idx'),
        ),
    ]
