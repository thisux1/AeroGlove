"""
Madgwick filter (IMU mode) for MicroPython on ESP32.

Inputs:
- gyroscope: rad/s (gx, gy, gz)
- accelerometer: g units (ax, ay, az), not necessarily normalized

Output quaternion kept in self.q (w, x, y, z) and helper to get Euler.
"""

from math import sqrt, atan2, asin


class MadgwickAHRS:
    def __init__(self, beta: float = 0.1):
        self.beta = beta
        self.q0 = 1.0
        self.q1 = 0.0
        self.q2 = 0.0
        self.q3 = 0.0

    def update_imu(self, gx: float, gy: float, gz: float, ax: float, ay: float, az: float, dt: float) -> None:
        q0 = self.q0
        q1 = self.q1
        q2 = self.q2
        q3 = self.q3

        # Normalize accelerometer
        norm = sqrt(ax * ax + ay * ay + az * az)
        if norm == 0.0:
            return
        ax /= norm
        ay /= norm
        az /= norm

        # Auxiliary variables to avoid repeated calculations
        _2q0 = 2.0 * q0
        _2q1 = 2.0 * q1
        _2q2 = 2.0 * q2
        _2q3 = 2.0 * q3
        _4q0 = 4.0 * q0
        _4q1 = 4.0 * q1
        _4q2 = 4.0 * q2
        _8q1 = 8.0 * q1
        _8q2 = 8.0 * q2
        q0q0 = q0 * q0
        q1q1 = q1 * q1
        q2q2 = q2 * q2
        q3q3 = q3 * q3

        # Gradient descent algorithm corrective step
        s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay
        s1 = _4q1 * q3q3 - _2q3 * ax + 4.0 * q0q0 * q1 - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az
        s2 = 4.0 * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az
        s3 = 4.0 * q1q1 * q3 - _2q1 * ax + 4.0 * q2q2 * q3 - _2q2 * ay
        norm_s = sqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3)
        if norm_s != 0.0:
            s0 /= norm_s
            s1 /= norm_s
            s2 /= norm_s
            s3 /= norm_s

        # Compute rate of change of quaternion
        qDot0 = 0.5 * (-q1 * gx - q2 * gy - q3 * gz) - self.beta * s0
        qDot1 = 0.5 * (q0 * gx + q2 * gz - q3 * gy) - self.beta * s1
        qDot2 = 0.5 * (q0 * gy - q1 * gz + q3 * gx) - self.beta * s2
        qDot3 = 0.5 * (q0 * gz + q1 * gy - q2 * gx) - self.beta * s3

        # Integrate to yield quaternion
        q0 += qDot0 * dt
        q1 += qDot1 * dt
        q2 += qDot2 * dt
        q3 += qDot3 * dt

        # Normalize quaternion
        norm_q = sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
        if norm_q == 0.0:
            return
        norm_q = 1.0 / norm_q
        self.q0 = q0 * norm_q
        self.q1 = q1 * norm_q
        self.q2 = q2 * norm_q
        self.q3 = q3 * norm_q

    def euler(self):
        # ZYX yaw-pitch-roll
        q0, q1, q2, q3 = self.q0, self.q1, self.q2, self.q3
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (q0 * q1 + q2 * q3)
        cosr_cosp = 1 - 2 * (q1 * q1 + q2 * q2)
        roll = atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (q0 * q2 - q3 * q1)
        if sinp >= 1:
            pitch = 1.57079632679
        elif sinp <= -1:
            pitch = -1.57079632679
        else:
            pitch = asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (q0 * q3 + q1 * q2)
        cosy_cosp = 1 - 2 * (q2 * q2 + q3 * q3)
        yaw = atan2(siny_cosp, cosy_cosp)
        return roll, pitch, yaw


