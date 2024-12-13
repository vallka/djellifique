from datetime import date,datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from prestashop.models import ProductInventory


db = 'presta'
id_shop = 1

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'product inventory'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print (self.help)
        logger.info(self.help)

        today = datetime.today().date() # get a Date object
        logger.info(today)

        self.main()

        print('done')
        logger.error("DONE - %s! - %s",self.help,str(today))

    def process_sheet(self,spreadsheet_id,service,sheet_title,first_row):
        products = []
        if 'ID' in first_row and 'kg' in first_row:
            idx = first_row.index('ID')
            kgx = first_row.index('kg')
            print(f"***id and kg: {idx}: {kgx}")
            data_range_name = f"{sheet_title}!A2:M"

            data = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=data_range_name
            ).execute()
            values = data.get('values', [])
            for row in values:
                if len(row)>idx and len(row)>kgx:
                    print(row[idx],row[kgx])
                    if row[idx]:
                        products.append({'ID':row[idx],'kg':row[kgx]})

        return products

    def main(self):
        SERVICE_ACCOUNT_FILE = '.gcredentials.json'
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        SPREADSHEET_ID = "1s3oOBQKGcSytND6xfbJW60DxD8CrlHFMtwHuIId2hmk"

        try:
            products = []

            service = build("sheets", "v4", credentials=credentials)
            spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            sheets = spreadsheet.get('sheets', [])

            # Iterate through each sheet
            for sheet in sheets:
                # Each sheet object contains a 'properties' object with details.
                sheet_properties = sheet.get('properties', {})
                sheet_title = sheet_properties.get('title', 'Untitled')

                print(f"Sheet Title: {sheet_title}")
                range_name = f"{sheet_title}!1:1"

                # Retrieve the first row of the sheet
                result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
                values = result.get('values', [])
                if values:
                    # values[0] represents the first row
                    first_row = values[0]
                    print(f"First row of {sheet_title}: {first_row}")

                    products += self.process_sheet(SPREADSHEET_ID,service,sheet_title,first_row)
                else:
                    print(f"No data found in the first row of {sheet_title}.")


            if products:
                print(products)
                productsd = {}
                for p in products:
                    if not productsd.get(p['ID']): 
                        productsd[p['ID']] = {}
                    if p['kg']: 
                        productsd[p['ID']]['kg'] = p['kg'] 


                print(productsd)

                for id,p in productsd.items():
                    print(id,p)


                    #try:
                    #    pi = ProductInventory.objects.get(id_product=int(p['ID']),inventory_type='to fill kg')
                    #    print(pi)
                    #    if pi.value!=p['kg']:
                    #        print(f"Updating {p['ID']} {p['kg']}")
                    #        pi.value = p['kg']
                    #        pi.save()
#
                    #except ProductInventory.DoesNotExist:
                    #    print(f"Adding {p['ID']} {p['kg']}")
                    #    pi = ProductInventory(id_product=int(p['ID']),inventory_type='to fill kg',value=p['kg'])
                    #    pi.save()

        except HttpError as err:
            print(err)
