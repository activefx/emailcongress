import os
from emailcongress import utils
import requests
import json
import traceback

from django.core.management.base import BaseCommand, CommandError

from emailcongress.models import Legislator
from django.conf import settings


def import_congresspeople(from_cache=False):
    """

    @param from_cache:
    @type from_cache:
    @return:
    @rtype:
    """
    if from_cache:  # load members of congress from cache (to speed up testing/development)
        with open(os.path.join(settings.BASE_DIR, settings.CONFIG_DICT['paths']['legislator_data_cache']), mode='r') as cache:
            data = json.load(cache)
            for leg in data:
                fields = {k: v for k, v in leg.items() if k in Legislator.CONGRESS_API_COLUMNS}
                Legislator.objects.get_or_create(**fields)

    # get all contactable reps from the phantom of the capitol database
    contactable = requests.get(settings.CONFIG_DICT['api_endpoints']['phantom_base'] + '/list-congress-members',
                               params={'debug_key': settings.CONFIG_DICT['api_keys']['phantom_debug']})

    # collect contactable reps bioguides
    bioguide_ids = [x['bioguide_id'] for x in contactable.json()]

    # marks those for whom we don't have a contact-congress yaml as uncontactable
    Legislator.objects.exclude(bioguide_id__in=bioguide_ids).update(contactable=False)

    if not utils.bool_eval(from_cache):
        # Create legislator entry for congresspeople for whom we don't have a database entry
        all_legislators = []
        for bgi in bioguide_ids:
            leg = Legislator.objects.get_or_instantiate(bioguide_id=bgi)
            try:
                r = requests.get(settings.CONFIG_DICT['api_endpoints']['congress_base'] + '/legislators',
                                 params={'bioguide_id': bgi, 'apikey': settings.CONFIG_DICT['api_keys']['sunlight']})
                data = r.json()['results'][0]
                data['email'] = Legislator.doctor_email(data.get('oc_email', ''))
                for attr in Legislator.CONGRESS_API_COLUMNS:
                    setattr(leg, attr, data.get(attr, ''))
                leg.email = data['email']
                leg.save()
                all_legislators.append(data)
            except KeyboardInterrupt:
                pass
            except:
                print("No data from congress api for : " + bgi)
                # TODO report
                continue

        # save data to cache in case we need to load it up again
        with open(os.path.join(settings.BASE_DIR, settings.CONFIG_DICT['paths']['legislator_data_cache']), mode='w') as cache:
            json.dump(all_legislators, cache, indent=4)


class Command(BaseCommand):
    help = 'Run daily tasks.'
    tasks = {
        'import_congresspeople': import_congresspeople
    }

    def add_arguments(self, parser):
        parser.add_argument('task', nargs=1, type=str)
        parser.add_argument('--kwargs', type=lambda kv: kv.split("="), dest='kwargs', nargs='*', default=[])

    def handle(self, **options):
        try:
            if options.get('task'):
                self.tasks.get(options.pop('task')[0])(**{item[0]: item[1] for item in options['kwargs']})
            else:
                for name, method in self.tasks.items():
                    method()
        except:
            print(traceback.format_exc())
            raise CommandError("Error running daily tasks.")
