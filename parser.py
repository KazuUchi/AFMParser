import numpy as np
import struct

def between(left, right, s):
    before,_,a = s.partition(left)
    a, _, after = a.partition(right)
    return a

def after(a, value):
    # Find and validate first part.
    pos_a = value.rfind(a)
    if pos_a == -1: return ""
    # Returns chars after the found string.
    adjusted_pos_a = pos_a + len(a)
    if adjusted_pos_a >= len(value): return ""
    return value[adjusted_pos_a:]

def get_number(str):
    l = []
    for t in str.split():
        try:
            l.append(float(t))
        except ValueError:
            pass
    return l

class AFMParser(object):

    def __init__(self, filename):
        self.filename = filename
        self.header = self._get_header()
        self.type_format = "h"
        self.scans = self.get_scans()
        self.zsens = self.get_zsens()
        self.zsens2 = self.get_zsens2()
        self.sx = self.get_xposition()
        self.sy = self.get_yposition()
        self.sz = self.get_zposition()


    def get_scans(self):
        scans = []
        scan_counter = -1
        for line in self.header:
            if line == "*Ciao image list":
                scan_counter += 1
                scans.append({})
            if scan_counter >= 0 and not line.startswith('*'):
                split = line.split(": ")
                try:
                    scans[scan_counter][split[0]] = split[1]
                except IndexError:
                    scans[scan_counter][split[0]] = None
        return scans

    def get_scale(self, layer):
        scal_data= self._find_in_header("@2:Z scale: V [Sens.")
        try:
            return float(between("(", " V/LSB)", scal_data[layer]))
        except IndexError:
            return 1.0

    def get_zsens(self):
        scal_data= self._find_in_header("Zsens:")
        try:
            return float(between("V ", " nm/V", scal_data[0]))
        except IndexError:
            return 1.0

    def get_zsens2(self):
        scal_data= self._find_in_header("ZsensSens:")
        try:
            return float(between("V ", " nm/V", scal_data[0]))
        except IndexError:
            return 1.0

    def get_xposition(self):
        scal_data= self._find_in_header("Stage X:")
        try:
            return float(after(": ", scal_data[0]))
        except IndexError:
            return 1.0

    def get_yposition(self):
        scal_data= self._find_in_header("Stage Y:")
        try:
            return float(after(": ", scal_data[0]))
        except IndexError:
            return 1.0

    def get_zposition(self):
        scal_data= self._find_in_header("Stage Z:")
        try:
            return float(after(": ", scal_data[0]))
        except IndexError:
            return 1.0


    def get_layer_name(self, layer=0):
        file_type_data = self.scans[layer]["@2:Image Data"]
        return between("\"", "\"", file_type_data[layer])

    def read_layer(self, layer=0):
        offset = int(self.scans[layer]["Data offset"])
        rows = int(self.scans[layer]["Number of lines"])
        cols = int(self.scans[layer]["Samps/line"])
        return np.rot90(self._read_at_offset(offset, rows, cols) * self.get_scale(layer))

    def get_size(self):
        scan_size = get_number(self._find_in_header("Scan Size")[0].split(": ")[1])[0]
        x_offset = get_number(self._find_in_header("X Offset")[0].split(": ")[1])[0]
        y_offset = get_number(self._find_in_header("Y Offset")[0].split(": ")[1])[0]

        return scan_size, x_offset, y_offset

    def _get_header(self):
        """
        Read the header into an array for easy lookup
        """
        file = open(self.filename, "r")
        res = []
        for line in file:
            trimmed = line.rstrip().replace("\\", "")
            res.append(trimmed)
            if "*File list end" in trimmed:
                break
        file.close()
        return res

    def _find_in_header(self, key):
        return [line for line in self.header if key in line]

    def _read_at_offset(self, offset, rows, cols):
        data_size = struct.calcsize(self.type_format)

        f = open(self.filename, "rb")
        f.seek(offset)
        data = np.zeros((rows, cols))
        num_elements = rows * cols
        try:
            index = col = row = 0
            while index < num_elements:
                value = f.read(data_size)
                try:
                    data[row][col] = struct.unpack(self.type_format, value)[0]
                except Exception:
                    pass

                if row == rows - 1:
                    col+=1
                    row=0
                else:
                    row+=1
                index += 1

        finally:
            f.close()
        return data
