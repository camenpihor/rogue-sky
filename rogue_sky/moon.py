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

import numpy as np

EPSILON_ = 23.4397
JAN_1_2000_UTC = datetime.datetime(2000, 1, 1, 12, tzinfo=datetime.timezone.utc)


def _degree_math(func, *degree):
    return func(*np.radians(degree))


def sin(degree):
    return _degree_math(np.sin, degree)


def cos(degree):
    return _degree_math(np.cos, degree)


def tan(degree):
    return _degree_math(np.tan, degree)


def get_sidereal_time(date):
    """Get sidereal time from clock time at location.

    Sidereal time is a time scale that is based on the Earth's rate of rotation measured
    relative to the fixed stars. rf. https://en.wikipedia.org/wiki/Sidereal_time

    rf. https://www.aa.quae.nl/en/reken/sterrentijd.html#1_8

    Formula:
        Θ = M_Earth + Π_Earth + (15° * (t + t_z)) mod 360

        where,
            M_Earth = mean anomaly of earth
            Π_Earth = how far past the perihelion and the ecliptic longitude of Earth
            t = hour of today's local datetime
            t_z = the amount of hours offset from UTC

    Parameters
    ----------
    date : datetime.datetime

    Returns
    -------
    float
    """
    M_Earth_ = get_mean_anomaly_earth(date=date)  # pylint: disable=invalid-name
    Pi_Earth_ = 102.937  # pylint: disable=invalid-name
    t_ = date.hour  # pylint: disable=invalid-name
    t_z_ = date.utcoffset().total_seconds() / (60 * 60)
    return (M_Earth_ + Pi_Earth_ + (15 * (t_ + t_z_))) % 360


def get_geocentric_ecliptical_coordinates(date):
    """Get the geocentric ecliptical coordinates of the moon.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#4

    Formula:
        λ = (
            (218.316 + (13.176396 * (d - d_0))) +
            (6.289 * sin(134.963 + (13.064993 * (d - d_0))))
        )
        β = 5.128 * sin(93.272 + (13.22935 * (d - d_0)))

        where,
            β = geocentric ecliptical latitude
            λ = geocentric ecliptical longitude
            d = today
            d_0 = January 1, 2000 12PM UTC

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

    beta_ = 5.128 * sin(93.272 + (13.22935 * d_delta_days))
    lambda_ = (218.316 + (13.176396 * d_delta_days)) + (
        6.289 * sin(134.963 + (13.064993 * d_delta_days))
    )
    return beta_, lambda_


def get_declination(date):
    """Get the declination of the moon from the date.

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
        np.arcsin(
            (sin(beta_) * cos(EPSILON_)) + (cos(beta_) * sin(EPSILON_) * sin(lambda_))
        )
    )


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
            (sin(lambda_) * cos(EPSILON_)) - (tan(beta_) * sin(EPSILON_)), cos(lambda_),
        )
    )


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


def get_hour_angle(date):
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
    theta_ = get_sidereal_time(date=date)
    alpha_ = get_right_ascension(date=date)
    return theta_ - alpha_


def get_altitude(date, latitude):
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
    """
    phi_ = latitude
    delta_ = get_declination(date=date)
    H_ = get_hour_angle(date=date)  # pylint: disable=invalid-name

    altitude_actual = np.degrees(
        np.arcsin((sin(phi_) * sin(delta_)) + (cos(phi_) * cos(delta_) * cos(H_)))
    )
    altitude_apparent = correct_altitude(altitude=altitude_actual)
    return altitude_apparent


def get_horizon_angle(date, latitude):
    """Get the hour angle of the horizon.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#2_2

    Formula:
        H_horizon = arccos((sin(h_0) − sin(φ)sin(δ)) / cos(φ)cos(δ))

        where,
            H_horizon = horizon hour angle
            h_0 = the height which we call the "horizon" (can change given refraction)
            φ = geographical latitude
            δ = declination

    Parameters
    ----------
    date : datetime.datetime
    latitude : float

    Returns
    -------
    float
    """
    h_0_ = 0
    phi_ = latitude
    delta_ = get_declination(date=date)
    return np.degrees(
        np.arccos((sin(h_0_) - (sin(phi_) * sin(delta_))) / (cos(phi_) * cos(delta_)))
    )


def get_transit_time(date, latitude):
    """Get the transit time of the Moon at location.

    The point at which the Moon passes the celestial meridian and is highest in the sky.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#2_1

    Formula:
        t_transit = ((α + l − M_Earth − Π_Earth) / 15) − t_z

        where,
            t_transit = time at which Moon is at the celestial meridian
            α = right ascension (how far the moon is from the vernal equinox)
            M_Earth = Mean Anomoly
            Π_Earth = 102.937
            t_z = the number of hours you'd have to add to local time to get to UTC

    Parameters
    ----------
    date : datetime.datetime
    latitiude : float

    Returns
    -------
    float
    """
    alpha_ = get_right_ascension(date=date)  # pylint: disable=invalid-name
    l_ = latitude  # pylint: disable=invalid-name
    M_Earth_ = get_mean_anomaly_earth(date=date)  # pylint: disable=invalid-name
    Pi_Earth_ = 102.937  # pylint: disable=invalid-name
    t_z_ = date.utcoffset().total_seconds() / (60 * 60)
    return ((alpha_ + l_ - M_Earth_ - Pi_Earth_) / 15) - t_z_


def get_rise_time(date, latitude, longitude):
    """Get the moon rise time, if happens, on date at location.

    rf. https://www.aa.quae.nl/en/reken/hemelpositie.html#2_2

    Formula:


    Parameters
    ----------
    date : datetime.datetime
        Should have timezone at location.
    latitude : float
        180-degree system
    longitude : float
        180-degree system
    """
    # initialize date and altitude
    d_0 = date.replace(hour=0, minute=0, second=0)
    h_0 = get_altitude(date=d_0, latitude=latitude)

    for hour in list(range(1, 24))[::2]:
        h_1 = get_altitude()
