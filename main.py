import time
import os
import json
from hashlib import sha256
import shutil
import sys
import csv

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
        # location of json database / library and other files
        self.home_dir: str = os.getcwd()
        self.main_library_file_hashes: dict = {}
        self.main_libary_json_file = os.path.join(self.home_dir, r'main_lib.json')

        self.main_library_files_changed: bool = False
        self.main_library_path = r'C:\Users\David\Pictures'
        self.image_file_exts = set(['.jpg','.bmp', '.mp4', '.png', '.tif', '.peg', '.gif', '.m4a', '.avi'])

        # self.Cleaned_dirs = []
        self.Total_bytes_saved: int = 0
        self.block_size: int = 65536
        self.count_cleaned:int = 0

    @staticmethod
    def write_filehashes_to_json(filehashes: dict, json_output_file: str) -> None:
        with open(json_output_file, 'w') as f:
            json.dump(filehashes, f, sort_keys=False)

    @staticmethod
    def read_filehashes_from_json(json_input_file: str) -> dict:
        if os.path.exists(json_input_file):
            with open(json_input_file, 'r') as f:
                return json.load(f)
        else:
            return {}

    # def load_prior_data(self) -> dict:
    #     """
    #     Loads data from 'all.json' in working directory into self.Filehashes
    #     :return:
    #     """
    #     # Load data from prior search
    #     json_input_file = os.path.join(self.home_dir, r'all.json')
    #     return self.read_filehashes_from_json(json_input_file)

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

    def add_hashes_for_files_in_tree(self, start_path: str, file_hashes: dict) -> None:
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
                    if filehash in file_hashes:
                        # already there so add this filespec to the dictionary of files
                        dups_of_this_file_dict = file_hashes[filehash]
                        dups_of_this_file_dict[full_filespec] = file_info_tuple
                    else:
                        # not there so create the hash and point it to a dict containting our first file
                        file_hashes[filehash] = {full_filespec: file_info_tuple}
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

        # load main library hashes
        if os.path.exists(self.main_libary_json_file):
            # load from json file
            self.main_library_file_hashes = self.read_filehashes_from_json(self.main_libary_json_file)
        else:
            # build from files to create hashes.
            self.main_library_files_changed = True
            self.add_hashes_for_files_in_tree(self.main_library_path, self.main_library_file_hashes)

        # load ext hd library hashes
        # %%%%%%%%%%%%%%%%%%%%%%% SET THIS %%%%%%%%%%%%%%%%%%
        ext_photo_library_path = r'E:'
        # ext_hd_vol_serial_no = '4ac0-ec0d'
        ext_hd_vol_serial_no = self.get_hard_drive_serial_for_path(ext_photo_library_path)
        ext_hd_json_file = os.path.join(self.home_dir, fr'hd {ext_hd_vol_serial_no}.json')

        # # create ext HD hashes
        # %%%%%%%%%%%%%%%%%%%%%%% SET THIS %%%%%%%%%%%%%%%%%%
        ext_hd_chars_to_trim_count = 3
        ext_hd_file_hashes = {}

        if os.path.exists(ext_hd_json_file):
            ext_hd_file_hashes = self.read_filehashes_from_json(ext_hd_json_file)
        else:
            self.add_hashes_for_files_in_tree(ext_photo_library_path, ext_hd_file_hashes)

            # # %%%%%%%%%%%%%%%%%%%%%%% SET THIS FOR EXTRA DIRS %%%%%%%%%%%%%%%%%%
            # ext_photo_library_path = r"D:\HAROLD'S BIOGRAPHY APRIL 2020"
            # self.add_hashes_for_files_in_tree(ext_photo_library_path, ext_hd_file_hashes)

            # save found hashes for ext drive
            self.write_filehashes_to_json(ext_hd_file_hashes, ext_hd_json_file)

        # search for ext hd hashes missing from main library and copy them to main library
        failed_copies = []
        for ext_hash in ext_hd_file_hashes.keys():
            if ext_hash not in self.main_library_file_hashes:
                file_info_dict = ext_hd_file_hashes[ext_hash]
                missing_src_file = sorted(list(file_info_dict.keys()), reverse=True)[0]
                if os.path.splitext(missing_src_file)[1] in self.image_file_exts:
                    # this is an image file so we need to copy it and add it to main library hashes
                    # add this file to list of missing image files

                    # add the file's hash to the main library hashes
                    new_file_spec = os.path.join(self.main_library_path, missing_src_file[ext_hd_chars_to_trim_count:])
                    self.main_library_file_hashes[ext_hash] = {new_file_spec: file_info_dict[missing_src_file]}
                    print(f'    copying file "{missing_src_file}" to "{new_file_spec}"')
                    # make sure the path we're copying to exists, if it's a new folder

                    if os.path.exists(new_file_spec):
                        print(f"  Skipped - already exists '{new_file_spec}'")
                    else:
                        try:
                            os.makedirs(os.path.dirname(new_file_spec), exist_ok=True)
                        except FileNotFoundError:
                            print(f"  %%%ERROR - unable to create folder to copy file '{missing_src_file}'")
                            failed_copies.append((missing_src_file, new_file_spec, sys.exc_info()))
                        except:
                            print(f"  %%%ERROR - unable to create folder to copy file '{missing_src_file}'")
                            print("Unexpected error:", sys.exc_info()[0])
                            failed_copies.append((missing_src_file, new_file_spec, sys.exc_info()))

                        try:
                            shutil.copyfile(missing_src_file, new_file_spec)
                        except FileNotFoundError:
                            print (f"  %%%ERROR - unable to locate source file to copy '{missing_src_file}'")
                            failed_copies.append((missing_src_file,new_file_spec, sys.exc_info()))
                        except:
                            print (f"  %%%ERROR - unable to copy file '{missing_src_file}'")
                            print("Unexpected error:", sys.exc_info()[0])
                            failed_copies.append((missing_src_file,new_file_spec, sys.exc_info()))

                    # flag that library hashes have changed and needs to be rewritten
                    self.main_library_files_changed = True
        # Write CSV file of files that failed to copy
        # opening the csv file in 'w+' mode
        file = open('failed to copy.csv', 'w+', newline='')

        # writing the data into the file
        with file:
            write = csv.writer(file)
            write.writerows(failed_copies)

        if self.main_library_files_changed:
            # rewrite main library hashes
            self.write_filehashes_to_json(self.main_library_file_hashes, self.main_libary_json_file)

        # dups = [(f, file_hashes[f]) for f in file_hashes if len(file_hashes[f]) > 1]
        # json_output_file = os.path.join(self.home_dir, r'dups.json')
        # self.write_filehashes_to_json(dups, json_output_file)
        #
        # with open(os.path.join(self.home_dir, r'all.json'), 'w') as f:
        #     json.dump(file_hashes, f, sort_keys=True)

        # Creates list of ALL files in self.Filehashes
        # all_files_list = list(flatten([list(file_hashes[f].keys()) for f in file_hashes]))
        # all_files_dict = dict().fromkeys(all_files_list)

        print ('Exiting')
        exit(0)

if __name__ == '__main__':
    App = Duplython()
    App.main()