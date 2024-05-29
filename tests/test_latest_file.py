import unittest
from datetime import date, timedelta, datetime
from platform_input_support.modules.common import extract_date_from_file


class TestLatestFile(unittest.TestCase):
    """
    The setup generates the date for the year 2021
    """
    def setUp(self):
        start_date = date(2021, 1, 1)  # start date
        end_date = date(2022, 1, 1)  # end date
        self.dates = []
        for n in range(int((end_date - start_date).days)):
            self.dates.append(start_date + timedelta(n))

    def test_no_date_found(self):
        filename = 'temp_cosmic007-0402-2021.json.gz'
        result = extract_date_from_file(filename)
        self.assertEqual(result, None)

    def test_wrong_format(self):
        expected_date = datetime(2021,2,4)
        filename = 'temp_cosmic0074-02-2021.json.gz'
        result = extract_date_from_file(filename)
        self.assertEqual(result, expected_date)

    def test_all_date_yyyy_mm_dd(self):
        """
        Test format yyyy-mm-dd all 2021 possible filename
        """
        for dt in self.dates:
            dt_expected = datetime.combine(dt, datetime.min.time())
            filename = 'temp_' + str(dt) + '.json.gz'
            result = extract_date_from_file(filename)
            self.assertEqual(result, dt_expected)

    def test_all_date_yyyy_m_d(self):
        """
        Test format when the date miss the 0 for months or days.
        Eg. 2021-2-10 / 2021-11-1 / 2021-1-1
        """
        for dt in self.dates:
            date_nozero = '{dt.year}-{dt.month}-{dt.day}'.format(dt=dt)
            # skip the date already tested above eg. "2021-10-10"
            if str(dt) != str(date_nozero):
                dt_expected = datetime.combine(dt, datetime.min.time())
                filename = 'temp_' + str(date_nozero) + '.json.gz'
                result = extract_date_from_file(filename)
                self.assertEqual(result, dt_expected)

    def test_all_date_dd_mm_yyyy(self):
        """
        Test format dd-mm-yyyy all 2021 possible filename
        """
        for dt in self.dates:
            dt_expected = datetime.combine(dt, datetime.min.time())
            date_reverse = dt.strftime('%d-%m-%Y')
            filename = 'temp_' + str(date_reverse) + '.json.gz'
            result = extract_date_from_file(filename)
            self.assertEqual(result, dt_expected)

    def test_all_date_d_m_yyyy(self):
        """
        Test format when the date miss the 0 for months or days.
        Eg. 2-10-2021 / 11-5-2021 / 1-1-2021
        """
        for dt in self.dates:
            date_reverse=dt.strftime('%d-%m-%Y')
            date_reverse_no_zero = '{dt.day}-{dt.month}-{dt.year}'.format(dt=dt)
            # skip the date already tested above eg. "10-10-2021"
            if str(date_reverse) != str(date_reverse_no_zero):
                dt_expected = datetime.combine(dt, datetime.min.time())
                filename = 'temp_' + str(date_reverse_no_zero) + '.json.gz'
                result = extract_date_from_file(filename)
                self.assertEqual(result, dt_expected)



