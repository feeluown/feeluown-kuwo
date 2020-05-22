from fuo_kuwo.utils import unsigned_right_shift


class KwDecrypt:
    CONST_1 = b'kwks&@69'

    @staticmethod
    def aba(b_arr: bytes, i: int):
        i7 = int(((i * 4) + 2) / 3)
        c_arr = bytes()
        i8 = 0
        i9 = 0
        while i8 < i:
            i10 = i8 + 1
            b4 = b_arr[i8]
            if i10 < i:
                i2 = i10 + 1
                b2 = b_arr[i10] & 255
            else:
                i2 = i10
                b2 = 0
            if i2 < i:
                i3 = i2 + 1
                b3 = b_arr[i2] & 255
            else:
                i3 = i2
                b3 = 0
            i11 = unsigned_right_shift(b4, 2)
            i12 = ((b4 & 3) << 4) | unsigned_right_shift(b2, 4)

