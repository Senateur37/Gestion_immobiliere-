"""Alignement des horodatages et des libelles sur TimeStampedModel."""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def horodater_les_lignes_existantes(apps, schema_editor):
    """Renseigne created_at avant de le rendre obligatoire."""
    LeaseTenant = apps.get_model('Locations', 'LeaseTenant')
    LeaseTenant.objects.filter(created_at__isnull=True).update(
        created_at=django.utils.timezone.now()
    )


def revenir_en_arriere(apps, schema_editor):
    """Rien a defaire."""


class Migration(migrations.Migration):

    dependencies = [
        ('Locations', '0003_organization'),
    ]

    operations = [
        migrations.RunPython(horodater_les_lignes_existantes, revenir_en_arriere),
        migrations.AlterField(
            model_name='leasetenant',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Cree le'),
        ),
        migrations.AlterField(
            model_name='leasetenant',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Mis a jour le'),
        ),
        migrations.AlterField(
            model_name='lease',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Mis a jour le'),
        ),
        migrations.AlterField(
            model_name='lease',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Cree le'),
        ),
        migrations.AlterField(
            model_name='inspection',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Cree le'),
        ),
        migrations.AlterField(
            model_name='inspection',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Mis a jour le'),
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
    ]
