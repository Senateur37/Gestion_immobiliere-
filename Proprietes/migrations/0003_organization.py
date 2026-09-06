"""Rattachement du patrimoine a une organisation.

En trois temps, parce que le champ est obligatoire alors que des lignes
existent deja : on ajoute la colonne nullable, on la remplit, puis on la
rend obligatoire. Une seule migration destructive evitee.
"""
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


def rattacher_a_une_organisation(apps, schema_editor):
    """Place le patrimoine existant dans une organisation.

    On ne cree une organisation que s'il y a effectivement quelque chose
    a rattacher : inutile d'en semer une dans chaque base de test.
    """
    Property = apps.get_model('Proprietes', 'Property')
    Unit = apps.get_model('Proprietes', 'Unit')
    PropertyImage = apps.get_model('Proprietes', 'PropertyImage')
    Organization = apps.get_model('organizations', 'Organization')
    Membership = apps.get_model('organizations', 'Membership')

    if not (Property.objects.exists() or Unit.objects.exists() or PropertyImage.objects.exists()):
        return

    organization = Organization.objects.first()
    if organization is None:
        organization = Organization.objects.create(
            name='Organisation principale',
            slug='organisation-principale',
            kind='agency',
            currency='XOF',
            country='Mali',
        )
        # Les proprietaires actuels des biens deviennent membres, sans
        # quoi plus personne n'accederait au patrimoine apres migration.
        proprietaires = (
            Property.objects.exclude(owner__isnull=True)
            .values_list('owner_id', flat=True)
            .distinct()
        )
        for index, owner_id in enumerate(proprietaires):
            Membership.objects.create(
                organization=organization,
                user_id=owner_id,
                role='owner',
                is_default=(index == 0),
            )

    Property.objects.filter(organization__isnull=True).update(organization=organization)
    Unit.objects.filter(organization__isnull=True).update(organization=organization)
    PropertyImage.objects.filter(organization__isnull=True).update(organization=organization)


def revenir_en_arriere(apps, schema_editor):
    """Rien a defaire : la colonne disparait avec le retour en arriere."""


class Migration(migrations.Migration):

    dependencies = [
        ('Proprietes', '0002_alter_property_address_alter_property_city_and_more'),
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. La colonne, encore facultative.
        migrations.AddField(
            model_name='property',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Proprietes_property_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AddField(
            model_name='unit',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Proprietes_unit_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AddField(
            model_name='propertyimage',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Proprietes_propertyimage_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AddField(
            model_name='propertyimage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Mis a jour le'),
        ),

        # 2. Le remplissage.
        migrations.RunPython(rattacher_a_une_organisation, revenir_en_arriere),

        # 3. La colonne devient obligatoire.
        migrations.AlterField(
            model_name='property',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Proprietes_property_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AlterField(
            model_name='unit',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Proprietes_unit_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AlterField(
            model_name='propertyimage',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='Proprietes_propertyimage_set',
                to='organizations.organization',
                verbose_name='Organisation',
            ),
        ),

        # owner n'est plus le vecteur d'isolation : il devient facultatif
        # et n'entraine plus la suppression du bien.
        migrations.AlterField(
            model_name='property',
            name='owner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='owned_properties',
                to=settings.AUTH_USER_MODEL,
                help_text="Proprietaire reel. L'acces est regi par l'organisation, pas par ce champ.",
                verbose_name='Proprietaire du bien',
            ),
        ),
        migrations.RemoveIndex(
            model_name='property',
            name='properties__owner_i_a56902_idx',
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['organization', 'is_active'], name='properties__organiz_2fa5c3_idx'),
        ),
    ]
