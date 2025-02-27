from cereal import car
from openpilot.selfdrive.car.wuling.values import CAR

Ecu = car.CarParams.Ecu


FINGERPRINTS = {
  CAR.ALMAS_RS_PRO: [{
    193: 8, 197: 8, 201: 8, 225: 8, 288: 5, 296: 8, 298: 8, 320: 4, 381: 8, 401: 8, 404: 8, 413: 8, 451: 8, 454: 8, 481: 8, 485: 8, 489: 8, 497: 8, 501: 8, 549: 8, 560: 8, 608: 8, 611: 8, 617: 8, 840: 6, 842: 6, 844: 6, 846: 6, 880: 8, 883: 8, 996: 8, 997: 8, 1041: 8, 1043: 8, 1045: 8, 1047: 8, 1053: 8, 1065: 8, 1217: 8, 1225: 8, 1341: 8, 1381: 8, 1406: 8, 1417: 8, 1538: 8, 1541: 8, 1543: 8, 1552: 8, 1569: 8
  }]
}


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
