"""Remplace l'identifiant numerique par l'UID dans les modules.

La migration 0002 avait rattache les lignes avec la cle primaire de
l'organisation. On bascule sur l'UID, plus stable : il survit a un export
puis reimport, ne renseigne pas sur le nombre d'organisations, et deux
installations ne peuvent pas produire le meme.

Fait maintenant, tant que les volumes sont faibles.
"""
from django.db import migrations

MODELES = [
    ('comptes', 'Compte'),
    ('comptabilite_ohada', 'CompteComptable'),
    ('comptabilite_ohada', 'EcritureComptable'),
    ('comptabilite_ohada', 'JournalComptable'),
    ('comptabilite_ohada', 'ExerciceComptable'),
    ('django_paie', 'EcheanceSalariale'),
    ('django_paie', 'PeriodePaie'),
    ('django_paie', 'ParametrePaie'),
    ('django_paie', 'VariablePaieMensuelle'),
    ('django_paie', 'ReglePaie'),
    ('rh', 'Employee'),
    ('rh', 'Department'),
]


def _convertir(apps, ancien_vers_nouveau):
    for app_label, nom in MODELES:
        try:
            modele = apps.get_model(app_label, nom)
        except LookupError:
            continue
        for ancien, nouveau in ancien_vers_nouveau.items():
            modele.objects.filter(entreprise_id=ancien).update(entreprise_id=nouveau)


def vers_uid(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    correspondance = {
        str(pk): str(uid)
        for pk, uid in Organization.objects.values_list('pk', 'uid')
    }
    _convertir(apps, correspondance)


def vers_cle_primaire(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    correspondance = {
        str(uid): str(pk)
        for pk, uid in Organization.objects.values_list('pk', 'uid')
    }
    _convertir(apps, correspondance)


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_organization_uid'),
    ]

    operations = [
        migrations.RunPython(vers_uid, vers_cle_primaire),
    ]
