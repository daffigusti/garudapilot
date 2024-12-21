from panda import Panda, calculate_checksum, DLC_TO_LEN

# chery test signal
# chery can fd serial panda

p = Panda(serial="040022001551323235353431")
p.set_safety_mode(Panda.SAFETY_ALLOUTPUT)
# p.set_safety_mode(33)
p.set_power_save(False)
p.set_can_data_speed_kbps(0,2000)
p.can_recv()

# p.set_safety_mode(Panda.SAFETY_SILENT)

p.can_send(0x1E3, b"\x50\x78\x00\x00\x00\x00\x08\xE3", 4)
p.can_send(0x360, b"\xC1\x60\x00\x01\x00\x00", 4)
p.can_send(0x360, b"\xC1\x60\x00\x01\x00\x00", 0)

# BISA
p.can_send(0x345, b"\x76\xBE\x00\x0C\xBE\xFE\x2A\xA5", 0)

# GAK BISA
p.can_send(0x345, b"\x76\xBE\x00\x0C\xBE\xFE\x2A\xA2", 0)

p.can_send(0x345, b"\x79\xE2\x00\x00\x00\x00\xE2\x51", 0)


p.can_send(0x345, b"\x76\x80\x00\x02\xF7\x01\x1F\x6E", 0)

# acc status with cc speed
p.can_send(0x387, b"\x00\x0a\x00\x12\x08\x05\xa0\x42", 0)

# acc status with alert cancel
p.can_send(0x387, b"\x10\x0a\x00\x12\x08\x05\xa0\x42", 0)


#acc status with active
p.can_send(0x387, b"\x00\x0a\x00\x12\x0c\x05\xa0\x42", 0)

#ACC TEMPORARY OFF BECAUSE BRAKE PRESSED
p.can_send(0x387, b"\x00\x0a\x00\x12\x04\x05\xa0\x42", 0)

#WARNING ICA EXIT
p.can_send(0x3FC, b"\x00\x00\x09\x2C\x1B\x10\x0A\x71", 0)

#CHANGE TO ACC MODE
p.can_send(0x3FC, b"\x00\x00\x09\x22\x1B\x10\x01\x4B", 0)

#CHANGE TO ICC MODE
p.can_send(0x3FC, b"\x00\x00\x09\x24\x1B\x10\x01\x4B", 0)

