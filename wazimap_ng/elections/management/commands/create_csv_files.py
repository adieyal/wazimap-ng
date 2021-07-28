import os
import glob
import pandas as pd

import django
from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic
from django.core.files import File

from wazimap_ng.datasets.models import Geography
from wazimap_ng.elections.config import Local


class Command(BaseCommand):

    def format_ward(self, ward):
        return ward.replace("Ward", "").strip()

    def format_municipality(self, geography):
        return geography.split("-")[0].strip()

    def format_province(self, geography, geographies):
        return geographies.get(geography.strip(), None)

    def create_keys(self, row):
        return [
            f"{row.Province}~{row.BallotType}~{row.PartyName}",
            f"{row.Municipality}~{row.BallotType}~{row.PartyName}",
            f"{row.Ward}~{row.BallotType}~{row.PartyName}",
        ]

    def write_csv(self, file_name, headers, data):
        df = pd.DataFrame(data, columns=headers)
        df.to_csv(file_name, index=False)

    def get_province_geo_codes(self):
        geographies = Geography.objects.filter(
            version="2016 Boundaries", level="province"
        ).values("name", "code")
        return {g["name"] : g["code"] for g in geographies}

    def handle(self, *args, **options):
        csv_files = glob.glob(f"{Local.CSV_FILES_INPUT}*.csv")
        headers = ["Geography", "BallotType", "PartyName", "Count"]
        geographies = self.get_province_geo_codes()
        for f in csv_files:
            filename = f.split("/")[-1].split(".")[0]
            output_folder = f"{Local.CSV_FILES_OUTPUT}{filename}"
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            province = {}
            municipality = {}
            ward = {}
            df = pd.read_csv(f)
            for row in df.itertuples():
                province_key, municipality_key, ward_key = self.create_keys(row)

                if province_key in province:
                    counts = province[province_key]["counts"]
                    counts = {
                        "RegisteredVoters": int(row.RegisteredVoters) + counts["RegisteredVoters"],
                        "SpoiltVotes": int(row.SpoiltVotes) + counts["SpoiltVotes"],
                        "TotalValidVotes": int(row.TotalValidVotes) + counts["TotalValidVotes"]
                    }

                    province[province_key]["counts"] = counts

                else:
                    province[province_key] = {
                        "counts": {
                            "RegisteredVoters": int(row.RegisteredVoters),
                            "SpoiltVotes": int(row.SpoiltVotes),
                            "TotalValidVotes": int(row.TotalValidVotes)
                        },
                        "values": [self.format_province(row.Province, geographies), row.BallotType, row.PartyName]
                    }

                if municipality_key in municipality:
                    counts = municipality[municipality_key]["counts"]
                    counts = {
                        "RegisteredVoters": int(row.RegisteredVoters) + counts["RegisteredVoters"],
                        "SpoiltVotes": int(row.SpoiltVotes) + counts["SpoiltVotes"],
                        "TotalValidVotes": int(row.TotalValidVotes) + counts["TotalValidVotes"]
                    }

                    municipality[municipality_key]["counts"] = counts

                else:
                    municipality[municipality_key] = {
                        "counts": {
                            "RegisteredVoters": int(row.RegisteredVoters),
                            "SpoiltVotes": int(row.SpoiltVotes),
                            "TotalValidVotes": int(row.TotalValidVotes)
                        },
                        "values": [self.format_municipality(row.Municipality), row.BallotType, row.PartyName]
                    }

                if ward_key in ward:
                    counts = ward[ward_key]["counts"]
                    counts = {
                        "RegisteredVoters": int(row.RegisteredVoters) + counts["RegisteredVoters"],
                        "SpoiltVotes": int(row.SpoiltVotes) + counts["SpoiltVotes"],
                        "TotalValidVotes": int(row.TotalValidVotes) + counts["TotalValidVotes"]
                    }

                    ward[ward_key]["counts"] = counts

                else:
                    ward[ward_key] = {
                        "counts": {
                            "RegisteredVoters": int(row.RegisteredVoters),
                            "SpoiltVotes": int(row.SpoiltVotes),
                            "TotalValidVotes": int(row.TotalValidVotes)
                        },
                        "values": [self.format_ward(row.Ward), row.BallotType, row.PartyName]
                    }

            data_to_write = {
                "RegisteredVoters" : [],
                "SpoiltVotes": [],
                "TotalValidVotes": []
            }
            for d in province.values():
                value = d["values"]
                for key, val in data_to_write.items():
                    data_to_write[key].append(value + [d["counts"][key]])

            for d in municipality.values():
                value = d["values"]
                for key, val in data_to_write.items():
                    data_to_write[key].append(value + [d["counts"][key]])

            for d in ward.values():
                value = d["values"]
                for key, val in data_to_write.items():
                    data_to_write[key].append(value + [d["counts"][key]])

            for key, val in data_to_write.items():
                self.write_csv(
                    f'{output_folder}/{key}.csv', headers, val
                )
        
