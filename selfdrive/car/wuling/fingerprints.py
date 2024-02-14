from cereal import car
from openpilot.selfdrive.car.wuling.values import CAR

Ecu = car.CarParams.Ecu

FW_VERSIONS = {
   CAR.ALMAS_RS_PRO: {
     (Ecu.engine, 0x7e0, None): [
       b'\xf1\x8b !\t\x10\xf1\x9410436987AA      '
     ],
     (Ecu.transmission, 0x7e1, None): [
       b'\xf1\x8b !\x10\x07\xf1\x95C0390011\xf1\x94  bfqa0501'
     ],
     (Ecu.fwdRadar, 0x726, None): [
       b'\xf1\x8b\x00\x00\x00\x00\xf1\x95SGMW.SW.A.3.0\xf1\x91\x01jz\xca'
     ],
     (Ecu.eps, 0x720, None): [
       b'\xf1\x8b210704\xf1\x95\x00\x00\x00y\xf1\x91\x01i\x0c\xf9\xf1\x94\x08"\t'
     ],
   }
}