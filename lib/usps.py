import requests
from bs4 import BeautifulSoup
from localflavor.us.us_states import USPS_CHOICES

CODE_TO_STATE = dict(USPS_CHOICES)


class USPSScraper():

    USPS_BASE_URL = 'https://tools.usps.com/go/ZipLookupResultsAction!input.action'

    @staticmethod
    def usps_request(self, **kwargs):

        # construct get parameters string
        params = {
            'resultMode': 0,
            'companyName': '',
            'address1': kwargs.get('street_address', ''),
            'address2': '',
            'city': kwargs.get('city', ''),
            'state': kwargs.get('state',''),
            'urbanCode': '',
            'postalCode': '',
            'zip': kwargs.get('zip5', '')
        }

        # make request. need to spoof headers or get infinite redirect
        return requests.get(self.USPS_BASE_URL, params=params, verify=False,
                            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36'
                                                   ' (KHTML, like Gecko) Chrome/39.0.2171.99 Safari/537.36'},
                            timeout=5)

    @staticmethod
    def usps_address_lookup(self, **kwargs):

        # parse html
        soup = BeautifulSoup(self.usps_request(**kwargs).text)

        # get container div for results
        results_content = soup.find(id='results-content')

        # build return dict
        address = {
            'street_address': '',
            'city': '',
            'state': '',
            'zip5': '',
            'zip4': ''
        }

        try:
            address['street_address'] = str(results_content.find('span', class_='address1').text).strip()
        except:
            print("Can't find street address")
        try:
            address['city'] = str(results_content.find('span', class_='city').text).strip().title()
        except:
            print("Can't find city")
        try:
            address['state'] = str(results_content.find('span', class_='state').text).strip()
        except:
            print("Can't find state")
        try:
            address['zip5'] = str(results_content.find('span', class_='zip').text).strip()
        except:
            print("Can't find zip5")
        try:
            address['zip4'] = str(results_content.find('span', class_='zip4').text).strip()
        except:
            print("Can't find zip4")

        return address

    def usps_zip_lookup(self, street_address, city, state, z5=''):
        """

        @param street_address: street address
        @type street_address: string
        @param city: city
        @type city: string
        @param state: state
        @type state: string
        @param z5: zip5
        @type z5: string
        @return: tuple of form (zip5, zip4)
        @rtype: tuple
        """

        address = self.usps_address_lookup(street_address=street_address, city=city, state=state, zip5=z5)
        return address['zip5'], address['zip4']