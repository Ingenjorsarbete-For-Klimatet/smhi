"""
SMHI unit tests.
"""
import pytest
from datetime import datetime
from functools import partial
from unittest.mock import patch
from smhi.strang import StrangPoint, check_date_validity, fetch_and_load_strang_data
from smhi.constants import (
    STRANG,
    STRANG_POINT_URL,
    STRANG_POINT_URL_TIME,
    STRANG_PARAMETERS,
    STRANG_DATE_FORMAT,
    STRANG_DATETIME_FORMAT,
    STRANG_TIME_INTERVALS,
)


CATEGORY = "strang1g"
VERSION = 1


class TestUnitStrangPoint:
    """
    Unit tests for STRÅNG Point class.
    """

    def test_unit_strang_init(self):
        """
        Unit test for STRÅNG Point init method.

        Args:
            mock_requests_get: mock requests get method
            mock_json_loads: mock json loads method
        """
        client = StrangPoint()

        assert client._category == CATEGORY
        assert client._version == VERSION

        assert client.latitude is None
        assert client.longitude is None
        assert client.parameter is None
        assert client.status is None
        assert client.header is None
        assert client.data is None

        assert (
            all(
                [x == y for x, y in zip(client.available_parameters, STRANG_PARAMETERS)]
            )
            is True
        )

        raw_url_dict = {"category": CATEGORY, "version": VERSION}
        for k1, k2 in zip(
            sorted(raw_url_dict.keys()), sorted(client.raw_url.keywords.keys())
        ):
            assert k1 == k2
            assert raw_url_dict[k1] == client.raw_url.keywords[k2]

        assert client.time_url is STRANG_POINT_URL_TIME
        assert client.url is None

    def test_unit_strang_parameters(self):
        """
        Unit test for STRÅNG Point parameters get property.
        """
        client = StrangPoint()
        assert (
            all([x == y for x, y in zip(client.parameters, STRANG_PARAMETERS)]) is True
        )

    @pytest.mark.parametrize(
        "lon, lat, parameter, time_from, time_to, time_interval",
        [
            (
                0,
                0,
                STRANG(
                    0,
                    None,
                    None,
                    None,
                ),
                "2020-01-01",
                "2020-01-01",
                "hourly",
            ),
            (
                0,
                0,
                STRANG_PARAMETERS[0],
                None,
                None,
                None,
            ),
            (
                0,
                0,
                STRANG_PARAMETERS[0],
                "2020-01-01",
                "2020-01-01",
                "hourly",
            ),
        ],
    )
    @patch("smhi.strang.check_date_validity")
    @patch("smhi.strang.fetch_and_load_strang_data", return_value=(1, 2, 3))
    def test_unit_strang_fetch_data(
        self,
        mock_fetch_and_load_strang_data,
        mock_check_date_validity,
        lon,
        lat,
        parameter,
        time_from,
        time_to,
        time_interval,
    ):
        """
        Unit test for STRÅNG Point fetch_data method.

        Args:
            mock_check_date_validity: mock check_date_validity method
            mock_fetch_and_load_strang_data: mock fetch_and_load_strang_data method
            lon: longitude
            lat: latitude
            parameter: parameter
            time_from: from time
            time_to: to time
            time_interval: time interval
        """
        client = StrangPoint()
        url = partial(STRANG_POINT_URL.format, category=CATEGORY, version=VERSION)
        time_url = STRANG_POINT_URL_TIME

        if parameter.parameter == 0:
            with pytest.raises(NotImplementedError):
                client.fetch_data(
                    lon,
                    lat,
                    parameter,
                    time_from,
                    time_to,
                    time_interval,
                )
        else:
            client.fetch_data(
                lon,
                lat,
                parameter,
                time_from,
                time_to,
                time_interval,
            )

            assert client.longitude == lon
            assert client.latitude == lat
            assert (
                client.parameter
                == [p for p in STRANG_PARAMETERS if p.parameter == parameter.parameter][
                    0
                ]
            )

            url = url(lon=lon, lat=lat, parameter=parameter.parameter)
            if time_from is not None:
                mock_check_date_validity.assert_called_once_with(
                    parameter,
                    url.format(
                        category=CATEGORY,
                        version=VERSION,
                        lon=lon,
                        lat=lat,
                        parameter=parameter.parameter,
                    ),
                    time_url,
                    time_from,
                    time_to,
                    time_interval,
                )
                mock_fetch_and_load_strang_data.assert_called_once_with(
                    mock_check_date_validity.return_value
                )
            else:
                assert url == client.url
                mock_fetch_and_load_strang_data.assert_called_once_with(url)

    def test_unit_strang_check_date_validity(self):
        """
        Unit test for STRANG Point check_date_validity function, type error and interval error.
        """
        parameter = STRANG_PARAMETERS[0]
        url = "URL"
        time_url = "URL_TIME"

        with pytest.raises(TypeError):
            time_from = "2020-01-01"
            time_to = None
            time_interval = "hourly"
            check_date_validity(
                parameter, url, time_url, time_from, time_to, time_interval
            )

        with pytest.raises(ValueError):
            time_from = "2020-01-01"
            time_to = "2022-01-01"
            time_interval = "minutly"
            check_date_validity(
                parameter, url, time_url, time_from, time_to, time_interval
            )

    @pytest.mark.parametrize(
        "time_from, time_to",
        [
            ("20222-01-01", "2022-01-01"),
            ("2022-012-01", "2022-01-01"),
            ("2022-01-012", "2022-01-01"),
            ("2022-01-01", "20222-01-01"),
            ("2022-01-01", "2022-012-01"),
            ("2022-01-01", "2022-01-012"),
            ("1900-01-01", "2022-01-01"),
            ("2010-01-01", "3000-01-01"),
            ("2010-01-01", "1900-01-01"),
            ("3000-01-01", "2022-01-01"),
        ],
    )
    def test_unit_strang_check_date_validity_valueerror(self, time_from, time_to):
        """
        Unit test for STRANG Point check_date_validity function, value error, bounds and format.

        Args:
            time_from: time from
            time_to: time to
        """
        parameter = STRANG_PARAMETERS[0]
        url = "URL"
        time_url = "URL_TIME"
        time_interval = "hourly"

        with pytest.raises(ValueError):
            check_date_validity(
                parameter, url, time_url, time_from, time_to, time_interval
            )

    def test_unit_strang_check_date_validity_correct(self):
        """
        Unit test for STRANG Point check_date_validity function, correct input.
        """
        parameter = STRANG_PARAMETERS[0]
        url = "URL"
        time_url = "{time_from} {time_to} {time_interval}"
        time_from = "2020-01-01"
        time_to = "2020-01-02"
        time_interval = "hourly"

        returned_url = check_date_validity(
            parameter, url, time_url, time_from, time_to, time_interval
        )

        assert returned_url == "URL2020-01-01 2020-01-02 hourly"

    @pytest.mark.parametrize(
        "ok, date_time",
        [
            (True, [{"date_time": "2020-01-01T00:00:00Z"}]),
            (False, [{"date_time": "2020-01-01T00:00:00Z"}]),
        ],
    )
    @patch(
        "smhi.strang.requests.get",
        return_value=type(
            "MyClass",
            (object,),
            {"ok": True, "headers": "header", "content": "content"},
        )(),
    )
    @patch(
        "smhi.strang.json.loads", return_value=[{"date_time": "2020-01-01T00:00:00Z"}]
    )
    def test_unit_strang_fetch_and_load_strang_data(
        self, mock_json_loads, mock_requests_get, ok, date_time
    ):
        """
        Unit test for STRANG Point fetch_and_load_strang_data function.

        Args:
            mock_requests_get: mock requests get method
            mock_json_loads: mock json loads method
            ok: request status
            date_time: date
        """
        url = "URL"
        mock_json_loads.return_value = date_time
        mock_requests_get.return_value.ok = ok
        status, headers, data = fetch_and_load_strang_data(url)
        mock_requests_get.assert_called_once_with(url)

        if ok is True:
            mock_json_loads.assert_called_once_with(
                mock_requests_get.return_value.content
            )
            assert status is ok
            assert headers == "header"
            assert data[0]["date_time"] == datetime.strptime(
                "2020-01-01T00:00:00Z", STRANG_DATETIME_FORMAT
            )

        else:
            assert status is ok
            assert headers == "header"
            assert data is None
