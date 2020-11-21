import time
import os
import json
from hashlib import sha256

r"""
1) Find all picture file types on the main drive in the OneDrive\Pictures folder
2) Calc a checksum for each
3) For all files with the same checksum, remove all duplicate files except the one with the longest pathname 
"""

def flatten(ob):
    for item in ob:
        if isinstance(item, (list, tuple, set)):
            yield from flatten(item)
        else:
            yield item

class Duplython:
    def __init__(self):
        self.home_dir = os.getcwd()
        self.File_hashes = {}
        # self.Cleaned_dirs = []
        self.Total_bytes_saved = 0
        self.block_size = 65536
        self.count_cleaned = 0

    def write_filehash_list_to_json(self, filehash_list: list, json_output_file: str) -> None:
        with open(json_output_file, 'w') as f:
            json.dump(filehash_list, f, sort_keys=False)

    def read_filehash_list_from_json(self, json_input_file: str) -> dict:
        if os.path.exists(json_input_file):
            with open(json_input_file, 'r') as f:
                return json.load(f)
        else:
            return {}

    def load_prior_data(self)-> None:
        """
        Loads data from 'all.json' in working directory into self.Filehashes
        :return:
        """
        # Load data from prior search
        json_input_file = os.path.join(os.getcwd(), r'all.json')
        self.File_hashes = self.read_filehash_list_from_json(json_input_file)

    def welcome(self) -> None:
        print('******************************************************************')
        print('****************        DUPLYTHON      ****************************')
        print('********************************************************************\n\n')
        print('----------------        WELCOME        ----------------------------')
        time.sleep(3)
        print('\nCleaning .................')

    def generate_hash(self, filename: str) -> str:
        filehash = sha256()
        try:
            with open(filename, 'rb') as File:
                fileblock = File.read(self.block_size)
                while len(fileblock) > 0:
                    filehash.update(fileblock)
                    fileblock = File.read(self.block_size)
                filehash = filehash.hexdigest()
            return filehash
        except:
            return None

    def get_hard_drive_serial_for_path(self, path: str) -> str:
        """
        Reads the serial number of the Hard Drive and returns in hex
        :param path: a path from which a hard drive letter can be derived
        :return: hard drive serial in hex.
        """
        # get drive letter from path
        drive = os.path.splitdrive(os.path.abspath(path))[0]
        serial = f'{os.stat(drive).st_dev:08x}'
        serial_with_dash = serial[0:4] + '-' + serial[4:9]

        return serial_with_dash

    def add_hashes_for_files_in_tree(self, start_path:str) -> None:
        vol_serial = self.get_hard_drive_serial_for_path(start_path)
        all_dirs = [path[0] for path in os.walk(start_path)]
        for path in all_dirs:
            # os.chdir(path)
            print(f'Scanning dir: {path}')
            all_files = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
            for file in all_files:
                full_filespec = os.path.join(path, file)
                file_size = os.path.getsize(full_filespec)
                filehash = self.generate_hash(full_filespec)
                if file_size and filehash:
                    # File hash has been created so check if in the dict
                    file_mod_date = os.path.getmtime(full_filespec)
                    # file_info_tuple = (full_filespec, file_mod_date, file_size)
                    file_info_tuple = (file_mod_date, file_size)
                    if filehash in self.File_hashes:
                        # already there so add this filespec to the dictionary of files
                        dups_of_this_file_dict = self.File_hashes[filehash]
                        dups_of_this_file_dict[full_filespec] = file_info_tuple
                    else:
                        # not there so create the hash and point it to a dict containting our first file
                        self.File_hashes[filehash] = {full_filespec: file_info_tuple}
                    print('  added ',file)
                else:
                    print('')

    def cleaning_summary(self) -> None:
        mb_saved = self.Total_bytes_saved / 1048576
        mb_saved = round(mb_saved, 2)
        print('\n\n--------------FINISHED CLEANING ------------')
        print('File cleaned  : ', self.count_cleaned)
        print('Total Space saved : ', mb_saved, 'MB')
        print('-----------------------------------------------')

    def main(self) -> None:
        self.welcome()
        self.load_prior_data()
        self.add_hashes_for_files_in_tree(r'D:\UD\OneDrive\Pictures')
        # dups = [(f, self.File_hashes[f]) for f in self.File_hashes if len(self.File_hashes[f]) > 1]
        dups = [(f, self.File_hashes[f]) for f in self.File_hashes if len(self.File_hashes[f]) > 1]
        json_output_file = os.path.join(os.getcwd(), r'dups.json')
        self.write_filehash_list_to_json(dups, json_output_file)

        with open(os.path.join(os.getcwd(), r'all.json'), 'w') as f:
            json.dump(self.File_hashes, f, sort_keys=True)

        # Creates list of ALL files in self.Filehashes
        # all_files_list = list(flatten([list(self.File_hashes[f].keys()) for f in self.File_hashes]))
        # all_files_dict = dict().fromkeys(all_files_list)

        print ('Exiting')
        exit(0)

if __name__ == '__main__':
    App = Duplython()
    App.main()