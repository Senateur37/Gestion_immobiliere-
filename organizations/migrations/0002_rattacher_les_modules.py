"""Rattache les lignes des modules metier a l'organisation.

Les modules ont ete installes avant que le rattachement automatique ne
soit en place : leurs lignes portent un entreprise_id vide. On les
rattache ici, une fois pour toutes, plutot que de laisser une reprise a
faire le jour du multi-entreprises.

S'il existe plusieurs organisations au moment de la migration, on ne
devine pas : la migration s'arrete et laisse la decision a un humain.
"""
from django.db import migrations

# Modeles a rattacher, par (application, modele).
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


def rattacher(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')

    organisations = list(Organization.objects.order_by('pk')[:2])
    if not organisations:
        return
    if len(organisations) > 1:
        raise RuntimeError(
            "Plusieurs organisations existent : le rattachement des lignes "
            "des modules ne peut pas etre devine. Rattachez-les a la main "
            "avant d'appliquer cette migration."
        )

    identifiant = str(organisations[0].pk)

    for app_label, nom in MODELES:
        try:
            modele = apps.get_model(app_label, nom)
        except LookupError:
            # Module non installe dans ce projet : rien a faire.
            continue
        modele.objects.filter(entreprise_id='').update(entreprise_id=identifiant)


def detacher(apps, schema_editor):
    """Retour en arriere : on vide le rattachement."""
    for app_label, nom in MODELES:
        try:
            modele = apps.get_model(app_label, nom)
        except LookupError:
            continue
        modele.objects.update(entreprise_id='')


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        ('comptes', '0005_compte_entreprise_id_alter_compte_code_and_more'),
        ('comptabilite_ohada', '0002_comptecomptable_entreprise_id_and_more'),
        ('rh', '0002_department_entreprise_id_employee_entreprise_id'),
    ]

    operations = [
        migrations.RunPython(rattacher, detacher),
    ]
