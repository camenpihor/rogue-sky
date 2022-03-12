"""Calculate the position and rising time of the moon.

Reference Material:
    https://www.aa.quae.nl/en/reken/hemelpositie.html

Variables:
     θ = sidereal time (time system based on rotation of the earth and fixed stars)
     H = hour angle (how far the moon has passed beyond the celestial meridian)
     δ = declination (how far the moon is from the celestial equator)
     α = right ascension (how far the moon is from the vernal equinox)
     ε = angle of the earth's axis of rotation to the earth's orbit path (23.4397°)
     β = geocentric ecliptical latitude
     λ = geocentric ecliptical longitude
     φ = geographical latitude (measured northward from the equator)
     l = geographical longitude (measured westward from Greenwich)

"""
import datetime
import logging

import numpy as np

EPSILON_ = 23.4397
JAN_1_2000_UTC = datetime.datetime(2000, 1, 1, 12, tzinfo=datetime.timezone.utc)

_logger = logging.getLogger(__name__)


def _degree_math(func, *degree):
    return func(*np.radians(degree))


def sin(degree):
    """Compute the sine where input is in degrees."""
    return _degree_math(np.sin, degree)


def cos(degree):
    """Compute the cosine where input is in degrees."""
    return _degree_math(np.cos, degree)


def tan(degree):
    """Compute the tangent where input is in degrees."""
    return _degree_math(np.tan, degree)


def get_geocentric_ecliptical_coordinates(date):
    """Get the geocentric ecliptical coordinates of the moon.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#4

    Formula:
        F = 93.272 + (13.229350 * (d - d0)) % 360
        L = 218.316 + (13.176396 * (d - d0)) % 360
        M = 134.963 + (13.064993 * (d - d0)) % 360

        λ = L + (6.289 * sin(M))
        β = 5.128 * sin(F)

        where,
            β = geocentric ecliptical latitude
            λ = geocentric ecliptical longitude
            d = today
            d_0 = January 1, 2000 12PM UTC
            F = average distance of the Moon from its ascending node
            L = average geocentric ecliptic longitude
            M = average anomaly

    Parameters
    ----------
    date: datetime.datetime

    Returns
    -------
    tuple
        (latitude, longitude)
    """
    d_ = date.astimezone(tz=datetime.timezone.utc)  # pylint: disable=invalid-name
    d_0_ = JAN_1_2000_UTC
    d_delta_days = (d_ - d_0_).total_seconds() / (24 * 60 * 60)

    F_ = (93.272 + (13.229350 * d_delta_days)) % 360  # pylint: disable=invalid-name
    L_ = (218.316 + (13.176396 * d_delta_days)) % 360  # pylint: disable=invalid-name
    M_ = (134.963 + (13.064993 * d_delta_days)) % 360  # pylint: disable=invalid-name

    beta_ = 5.128 * sin(F_)
    lambda_ = L_ + (6.289 * sin(M_))
    return beta_, lambda_


def get_sidereal_time(date, longitude):
    """Get sidereal time from clock time at location.

    Sidereal time is a time scale that is based on the Earth's rate of rotation measured
    relative to the fixed stars. rf. https://en.wikipedia.org/wiki/Sidereal_time

    rf. https://www.aa.quae.nl/en/reken/sterrentijd.html#1_8

    Formula:
        Θ = M_Earth + Π_Earth + (15° * (t + t_z)) mod 360
        sidereal_time = Θ - l

        where,
            Θ = sidereal time on the prime meridian
            M_Earth = mean anomaly of earth
            Π_Earth = how far past the perihelion and the ecliptic longitude of Earth
            t = hour of today's local datetime
            t_z = the amount of hours offset from UTC
            l = geographical longitude

    Parameters
    ----------
    date : datetime.datetime
    longitude : float

    Returns
    -------
    float
    """
    M_Earth_ = get_mean_anomaly_earth(date=date)  # pylint: disable=invalid-name
    Pi_Earth_ = 102.937  # pylint: disable=invalid-name
    t_ = date.hour  # pylint: disable=invalid-name
    t_z_ = -date.utcoffset().total_seconds() / (60 * 60)
    # pylint: disable=invalid-name
    Theta_ = (M_Earth_ + Pi_Earth_ + (15 * (t_ + t_z_))) % 360
    sidereal_time = (Theta_ - longitude) % 360
    return sidereal_time


def get_mean_anomaly_earth(date):
    """Get the average angle the earth traverses as seen from the Sun.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#1_1

    Formula:
        M = M_0 + (n * (d − d_0)) mod 360

        where,
            M = mean anomaly of earth
            M_0 = the initial mean anomaly of Earth on January 1, 2000 12pm UTC
            n = the average change of the angle per day
            d = today's date in UTC
            d_0 = January 1, 2000 12pm UTC

    Parameters
    ----------
    date : datetime.datetime

    Returns
    -------
    float
    """
    d_ = date.astimezone(datetime.timezone.utc)  # pylint: disable=invalid-name
    d_0_ = JAN_1_2000_UTC

    d_delta_days = (d_ - d_0_).total_seconds() / (24 * 60 * 60)
    return (357.529 + (0.985608 * d_delta_days)) % 360


def get_declination(date):
    """Get the how far the moon is from the celestial equator.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#1_7

    Formula:
        δ = arcsin(sin(β)cos(ε) + cos(β)sin(ε)sin(λ))

        where,
            δ = declination
            β = geocentric ecliptical latitude
            λ = geocentric ecliptical longitude
            ε = 23.4397°

    Parameters
    ----------
    date : datetime.datetime

    Returns
    -------
    float
    """
    beta_, lambda_ = get_geocentric_ecliptical_coordinates(date=date)
    return np.degrees(
        np.arcsin((sin(beta_) * cos(EPSILON_)) + (cos(beta_) * sin(EPSILON_) * sin(lambda_)))
    )


def get_right_ascension(date):
    """Get the right ascension of the moon from the date.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#1_7

    Formula:
        α = arctan2(sin(λ)cos(ε) − tan(β)sin(ε), cos(λ))

        where,
            α = right ascension
            β = geocentric ecliptical latitude
            λ = geocentric ecliptical longitude
            ε = 23.4397°

    Parameters
    ----------
    date : datetime.datetime

    Returns
    -------
    float
    """
    beta_, lambda_ = get_geocentric_ecliptical_coordinates(date=date)
    return np.degrees(
        np.arctan2(
            (sin(lambda_) * cos(EPSILON_)) - (tan(beta_) * sin(EPSILON_)),
            cos(lambda_),
        )
    )


def get_hour_angle(date, longitude):
    """Get the hour angle of the moon at time and location.

    The Hour angle indicates how far the moon has passed beyond the celestial meridian.
    If 0, then its at its peak.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#1_9

    Formula:
        H = θ − α

        where,
            H = hour angle
            θ = sidereal time
            α = right ascension

    Parameters
    ----------
    date : datetime.datetime

    Returns
    -------
    float

    """
    theta_ = get_sidereal_time(date=date, longitude=longitude)
    alpha_ = get_right_ascension(date=date)
    return theta_ - alpha_


def correct_altitude(altitude):
    """Correct the actual altitude of the moon due to light refraction.

    The atmosphere of the Earth bends light upward such that the moon appears higher in
    the sky than it otherwise would.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#1_10

    Formula:
        h_c = h + (0.017 / (tan(h + (10.26 / (h + 5.10)))))

        where,
            h_c = corrected altitude
            h = altitude

    Parameters
    ----------
    altitude : float

    Returns
    -------
    float
    """
    h_ = altitude  # pylint: disable=invalid-name
    return h_ + (0.017 / (tan(h_ + (10.26 / (h_ + 5.10)))))


def get_altitude(date, latitude, longitude):
    """Get the moon's altitude by an observer on Earth at date and location.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html1_10

    Formula:
        altitude = arcsin(sin(φ)sin(δ) + cos(φ)cos(δ)cos(H))

        where,
            φ = geographical latitude
            δ = declination
            H = hour angle

    Parameters
    ----------
    date : datetime.datetime
    latitude : float
    longitude : float
    """
    phi_ = latitude
    delta_ = get_declination(date=date)
    H_ = get_hour_angle(date=date, longitude=longitude)  # pylint: disable=invalid-name

    altitude_actual = np.degrees(
        np.arcsin((sin(phi_) * sin(delta_)) + (cos(phi_) * cos(delta_) * cos(H_)))
    )
    altitude_apparent = correct_altitude(altitude=altitude_actual)
    return altitude_apparent


def round_time(time):
    """Round time to the nearest minute."""
    seconds = time.second
    minutes = time.minute if seconds < 30 else time.minute + 1
    hours = time.hour
    if minutes == 60:
        hours += 1
        minutes = 0
    return time.replace(hour=hours, minute=minutes, second=0, microsecond=0)


def solve_2d_quadratic(x, y):
    """Solve for the roots of a 2d quadratic fitting `x` and `y`.

    Include whether the slope is increasing or decreasing at root, and
    only return roots that are within the interval [x[0], x[1]].

    Solve for ax^2 + bx + x c = 0, which should have 2 roots.
    To determine the slope at root, take the deriviative of the quadratic
    (2ax + b) and determine if that's positive (ascending) or negative
    (descending) at point.

    Parameters
    ----------
    x : array-like
        Must be the same shape as `y`.
    y : array-like
        Must be the same shape as `x`.

    Returns
    -------
    list of dict
        [
            {
                "value": float,
                "ascending": boolean
            }
        ]
    """
    a, b, c = np.polyfit(x, y, 2)  # pylint: disable=invalid-name
    roots = np.roots([a, b, c])

    return [
        {"value": root, "ascending": (2 * a * root) + b > 0}
        for root in roots
        if x[0] < root < x[-1]
    ]


def get_rise_time(local_date, latitude, longitude):
    """Get the time of moon rise at the local date and coordinates.

    rf. http://www.stargazing.net/kepler/moonrise.html

    Forumla:
        (1) calculate the sine of the altitude for the first 3 hours of the day
            times: (d_0, d_1, d_2); altitudes at times (h_0, h_1, h_2)
        (2) determine if the path of the altitude made by the 3 points
            (h_0, h_1, h_2) passes 0, which is the horizon.
            (2.1) if so, find the point at which altitude = 0
                (2.1.1) if slope is ascending at point, return and exit
                (2.1.2) else go to step (2.3)
            (2.2) if not,
                (2.2.1) if d_0 > 24 return None and exit
                (2.2.2) else go to step (2.3)
            (2.3) repeat step (2) using the next 3 hours starting at d_2:
                d_0 = d_2
                d_1 = d_0 + 1 hour
                d_2 = d_0 + 2 hours
                h_0 = h_2
                h_1 = altitude(d_1)
                h_2 = altitude(d_2)

    Parameters
    ----------
    local_date : datetime.datetime
        Should be in the timezone of coordinates.
    latitude : float
        Must be in decimal 180-degree system.
    longitude : float
        Must be in decimal 180-degree system.

    Returns
    -------
    datetime.datetime | None
        Returns `None` if no moon rise is supposed to predicted to occur on
        the date in the timezone of of `local_date`.
    """
    longitude = -longitude  # this algorithm uses westward longitude
    date = local_date.replace(hour=0, minute=0, second=0, microsecond=0)

    rise = None
    d_0 = date
    h_0 = np.radians(get_altitude(date=d_0, latitude=latitude, longitude=longitude))
    for i in range(1, 24, 2):
        d_1 = d_0 + datetime.timedelta(hours=1)
        h_1 = np.radians(get_altitude(date=d_1, latitude=latitude, longitude=longitude))

        d_2 = d_0 + datetime.timedelta(hours=2)
        h_2 = np.radians(get_altitude(date=d_2, latitude=latitude, longitude=longitude))

        x = [i - 1, i, i + 1]
        y = [h_0, h_1, h_2]
        for root in solve_2d_quadratic(x, y):
            if root["ascending"]:
                if isinstance(root["value"], np.complex128):
                    _logger.info(root)

                rise = date + datetime.timedelta(hours=root["value"])
                break

        if rise:
            break

        d_0 = d_2
        h_0 = h_2

    rise = round_time(rise) if rise else rise
    return rise


def phase_to_illumination(phase):
    """Calculate the moon illumination from the moon phase.

    "Illumination" is how full the moon is. Whereas moon phase describes both how full
    the moon is, but also whether it is waxing or waning.

    New Moon:           Phase 0 or 1    Illumination 0
    Half Moon Waxing:   Phase 0.25      Illumination 0.5
    Full Moon:          Phase 0.5       Illunmination 1
    Half Moon Waning:   Phase 0.75      Illumination 0.5

    rf. https://idlastro.gsfc.nasa.gov/ftp/pro/astro/mphase.pro

    Parameters
    ----------
    phase : float
        0 to 1

    Returns
    -------
    float
        0 to 1
    """
    return (1 + np.cos(((phase - 0.5) * np.pi) / 0.5)) / 2
