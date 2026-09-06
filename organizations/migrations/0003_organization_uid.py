"""Identifiant stable des organisations.

Les modules metier stockent un `entreprise_id`. Y mettre la cle primaire
serait fragile : elle change lors d'un export puis reimport, elle
renseigne sur le nombre d'organisations, et deux installations
produiraient les memes valeurs.

On ajoute donc un UUID, en trois temps puisque le champ est unique et que
des lignes existent deja : colonne facultative, remplissage, contrainte.
"""
import uuid

from django.db import migrations, models


def attribuer_les_uid(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    for organisation in Organization.objects.filter(uid__isnull=True):
        organisation.uid = uuid.uuid4()
        organisation.save(update_fields=['uid'])


def revenir_en_arriere(apps, schema_editor):
    """Rien a defaire : la colonne disparait avec le retour en arriere."""


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_rattacher_les_modules'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='uid',
            field=models.UUIDField(null=True, editable=False, verbose_name='UID'),
        ),
        migrations.RunPython(attribuer_les_uid, revenir_en_arriere),
        migrations.AlterField(
            model_name='organization',
            name='uid',
            field=models.UUIDField(
                default=uuid.uuid4, unique=True, editable=False, verbose_name='UID'
            ),
        ),
    ]
