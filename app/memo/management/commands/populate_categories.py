from django.core.management.base import BaseCommand

from app.memo.models import ElektriskKategori


class Command(BaseCommand):
    help = "Populate initial electrical categories based on Norwegian electrical numbering system"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        initial_categories = [
            {
                "blokknummer": "10",
                "kategori": "Kabler og ledninger",
                "beskrivelse": "Alle typer kabler og ledninger, støpemasse m/tilbehør for varmekabel med unntak av wire, kobbertråd og konfeksjonerte produkter.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "11",
                "kategori": "Kabelmuffer og kabelfordelingsskap",
                "beskrivelse": "Alle typer kabelmuffer, overgangshoder, endeavslutninger, kabelskritt, kabelmasse og kabelfordelingsskap m/tilbehør. Inntaksskap, se gruppe 17.",
                "etim_gruppe": "EC001xxx",
            },
            {
                "blokknummer": "12",
                "kategori": "Rør, tak- og veggbokser, koblingsmateriell, kanalsystemer",
                "beskrivelse": "Materiell for skjult forlegging, koblingsbokser, koblingsklemmer, pakknipler, stigeledningsklemmer, jordingsklemmer, jordingspunkt, rekkeklemmer, el-lister, kanalsystemer (gulv-vegg), branntetting og grenstaver.",
                "etim_gruppe": "EC002xxx",
            },
            {
                "blokknummer": "13",
                "kategori": "Festemateriell, kabelstiger og kabelrenner",
                "beskrivelse": "Festemateriell for rør, ledninger og kabel, stift, skruer, festeplugger, rørbeskyttere, festebånd, kabelbroer og armaturskinner m/utstyr.",
                "etim_gruppe": "EC000517",
            },
            {
                "blokknummer": "14",
                "kategori": "Brytere",
                "beskrivelse": "Installasjonsbrytere/vendere, hovedbrytere, reguleringsbrytere, kambrytere, sikkerhetsbrytere, effektregulatorer (dimmere), fjernbrytere, urbrytere, ledningsbrytere, brytere for skapmontasje, trappeautomater, lysstyringssystem (ikke BUSsystem) IR-sender/mottaker, fotoceller, bevegelsesvoktere, releer for styring av lys.",
                "etim_gruppe": "EC001744",
            },
            {
                "blokknummer": "15",
                "kategori": "Stikkontakter, støpsler m.m.",
                "beskrivelse": "Installasjon/industristikkontakter, støpsler, skjøtekontakter, skjøteledninger, kabelvinder, motorvarmesentraler, sentraler for provisoriske anlegg, multikontakter (sterkstrøm), stikkontakter for tavlemontasje, lampestikk-kontakter og SELFstikkontakter.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "16",
                "kategori": "Sikringsmateriell",
                "beskrivelse": "Sikringselementer/lokk, patroner, bunnskruer, sikrings- underdeler, glassikringer, elementautomater, overspenningsvern, automatsikringer, jordfeilbrytere, jordfeilvarsler/releer, sikringslister, høyeffektpatroner, betjeningshåndtak, sikringsskillebrytere og sølvtrådlameller.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "17",
                "kategori": "Sikringsbokser og -skap/sikringsstativer",
                "beskrivelse": "Inntak og målerskap m/tilbehør, sikringsskap m/tilbehør, installasjonsskap m/målerplass, universalstativer m/tilbehør, småfordelerskap, Cu-lisser og skinner, vibrodempere, vegg- gjennomføringer (porselen).",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "18",
                "kategori": "Isolasjons- og loddemateriell, merkingsutstyr, krympeslange",
                "beskrivelse": "Isolasjonsbånd, PVC-bånd, plaststrømpe, tetningsmasse, loddetinn/pasta, kjemiske væsker for rensing og isolasjon, merkehylser, merkekort, merkenåler, tekstmaskiner, glidemiddel.",
                "etim_gruppe": "EC001855",
            },
            {
                "blokknummer": "20",
                "kategori": "Kontaktpressingsmateriell og pressverktøy for samme",
                "beskrivelse": "Termittsveis",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "24",
                "kategori": "Plateskap med tilbehør i stål og aluminium",
                "beskrivelse": "Tavle og skapsystemer m/tilbehør, apparatskap og elektronikkskap m/tilbehør.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "25",
                "kategori": "Skap med tilbehør i silumin og isolerstoff",
                "beskrivelse": "Tette kapslinger m/tilbehør.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "28",
                "kategori": "Linjemateriell",
                "beskrivelse": "Linjemateriell",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "29",
                "kategori": "Materiell for innendørs montasje, 12kV og høyere spenninger",
                "beskrivelse": "Materiell for innendørs montasje, 12kV og høyere spenninger",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "30",
                "kategori": "Glødelampearmaturer, innendørs",
                "beskrivelse": "Lampeholdere, nipler, tak/vegglamper, pendler, tak/veggbeslag (åpne og tette), skottlamper, kupler og glass, håndlamper, arbeidslamper, strømskinner (sterkstrøm), spotlight, downlight og uplights for glødelamper.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "31",
                "kategori": "Glødelampearmaturer, utendørs",
                "beskrivelse": "Glødelampearmaturer, utendørs",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "32",
                "kategori": "Lyskastere og effektbelysning",
                "beskrivelse": "Lyskastere og undervannslyskastere, spot-, down- og uplights m/tilbehør, strømskinner for lav-volt og tilhørende transformatorer og spot-, down- og uplights for LED lyskilder.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "33",
                "kategori": "Lysrørarmatur og tilbehør",
                "beskrivelse": "Lysrørarmatur og tilbehør",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "35",
                "kategori": "Armaturer for natrium-, metalldamplamper og ledlamper",
                "beskrivelse": "Industriarmaturer, interiørarmaturer, gate og veilysarmaturer, kandelaberarmaturer, tunnelarmaturer, vandalarmaturer, park- og miljøarmatur, forkoblingsutstyr.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "36",
                "kategori": "Stålrørmaster og stolpearmer",
                "beskrivelse": "Fundamenter, stolpeinnsatser, avskjæringsledd, gittermaster og sikringsinnsatser for master.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "37",
                "kategori": "Glødelamper, halogenlamper, LED lamper",
                "beskrivelse": "Alle typer glødelamper, halogenlamper, glimlamper, varmelamper, høyfjellsoler, juletrebelysning, reflektorlamper, ledlamper og billamper",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "38",
                "kategori": "Lysrør og damplamper",
                "beskrivelse": "Alle typer lysrør og damplamper inkl. startere og kompaktlysrør.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "40",
                "kategori": "Motorer",
                "beskrivelse": "Motorer",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "41",
                "kategori": "Startapparater",
                "beskrivelse": "Kontaktorer, hjelpereleer, kontaktorkombinasjoner, mykstartere, frekvensstyring-og omformere.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "43",
                "kategori": "Styreorganer, motorvernbrytere, effektbrytere",
                "beskrivelse": "Motorvernbrytere, effektbrytere, betjeningsmateriell, signallamper, fotoceller og givere for industrielt bruk, timetellere, turtallsvakter, endebrytere og releer.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "45",
                "kategori": "Elektroniske styresystemer (PLS) etc.",
                "beskrivelse": "Maksimalvoktere, BUS-produkter (45 400 00-45 999 99), elektroniske signalomformere.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "49",
                "kategori": "Vifter, varmevifter og pumper",
                "beskrivelse": "Tak-, rom og kanalvifter, stasjonære og transportable varmevifter, varmluftsperrer, regulatorer, romhygrostater.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "53",
                "kategori": "Elektriske kokeapparater",
                "beskrivelse": "Komfyrer, bordkomfyrer.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "54",
                "kategori": "Elektrovarme og termostater",
                "beskrivelse": "Varmeovner, varmelister, panelovner, badstuovner m/tilbehør, takvarmesystemer, termostater, elektroniske effektregulatorer, snøsmelteutstyr, elementkjøler, varmefolie.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "56",
                "kategori": "Kjøle-/fryseskap og matbodkjølere m/tilbehør",
                "beskrivelse": "Kjøle-/fryseskap og matbodkjølere m/tilbehør",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "57",
                "kategori": "Vaskemaskiner og oppvaskmaskiner",
                "beskrivelse": "Vaskemaskiner og oppvaskmaskiner",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "58",
                "kategori": "Elektriske husholdningsapparater",
                "beskrivelse": "Strykejern, kaffetraktere, mikser, støvsugere, hårtørrere etc. gjerdeapparater, ur, hånd og håndkletørkere.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "59",
                "kategori": "Spesialpakket (blister-pakket) el-materiell for salg over disk",
                "beskrivelse": "Spesialpakket (blister-pakket) el-materiell for salg over disk",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "62",
                "kategori": "Signalutstyr og alarmsystemer",
                "beskrivelse": "Ringemateriell, sirener, horn, batterier, alarmsystemer, klokker, røykdetektorer, ringeknapper, ringetransformatorer, garasjeportåpnere.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "63",
                "kategori": "Signaldistribusjonsanlegg",
                "beskrivelse": "Kontorsignaler, personsøkeanlegg, uranlegg, lyssignalanlegg, lydanlegg, sykesignalanlegg, bildeanlegg, porttelefon, høyttalere. Overvåkningsutstyr.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "64",
                "kategori": "Kommunikasjonsapparater",
                "beskrivelse": "Telefon-, calling-,data-,fiber-apparater, sentraler, modem, telefax, nettverksprodukter, tranceivere, radioer, etc.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "65",
                "kategori": "Antennemateriell",
                "beskrivelse": "Antenner m/tilbehør, antennekontakter, apparatkabler, antenneplugger, fordelere, connectorer og satelittmottakings-utstyr.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "66",
                "kategori": "Strømforsyninger, nødlysanlegg og transformatorer",
                "beskrivelse": "Ladelikerettere, signaltransformatorer, avbruddsfri- kraft, nød- og markeringslys, transformatorer for halogenbelysning, batteriladere, styrestrømstransformatorer.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "69",
                "kategori": "Koblingsmateriell for tele/data",
                "beskrivelse": "Plinter, kontakter, kontaktpaneler, koblingsbokser, koblingssystemer, fiberoptikk, patchkabel, patchpanel, overspenningsvern, tilbehør til tele- og datautstyr.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "80",
                "kategori": "Instrumenter",
                "beskrivelse": "Kjøkkenwattmetere, tavleinstrumenter, transportable driftsinstrumenter, måletransformatorer.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "82",
                "kategori": "Målere og måleromkoblere",
                "beskrivelse": "Målere og måleromkoblere",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "86",
                "kategori": "Kondensatorer",
                "beskrivelse": "Motorkondensatorer, fasekompenseringskondensatorer, reguleringsutstyr for fasekompensering.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "88",
                "kategori": "Verktøy",
                "beskrivelse": "All slags verktøy med unntak av pressverktøy se gr. 20.",
                "etim_gruppe": "EC000000",
            },
        ]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        created_count = 0
        updated_count = 0

        for category_data in initial_categories:
            blokknummer = category_data["blokknummer"]

            if dry_run:
                existing = ElektriskKategori.objects.filter(
                    blokknummer=blokknummer
                ).exists()
                if existing:
                    self.stdout.write(
                        f"Would update: {blokknummer} - {category_data['kategori']}"
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        f"Would create: {blokknummer} - {category_data['kategori']}"
                    )
                    created_count += 1
            else:
                category, created = ElektriskKategori.objects.get_or_create(
                    blokknummer=blokknummer, defaults=category_data
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created: {category}"))
                    created_count += 1
                else:
                    # Update existing category with new data
                    for field, value in category_data.items():
                        if field != "blokknummer":
                            setattr(category, field, value)
                    category.save()
                    self.stdout.write(self.style.WARNING(f"Updated: {category}"))
                    updated_count += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN COMPLETE - Would create {created_count} and update {updated_count} categories"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {created_count} and updated {updated_count} electrical categories"
                )
            )
