import os
import argparse
from client import LvsApiClient


class DeleteSearchableClips:
    def __init__(self, api_key, username, password):
        self.lvs_client = LvsApiClient(api_key, username, password)

    def set_asset_id(self, asset_id):
        self.asset_id = asset_id

    def start_deleting_searchable_clips(self):
        return self.lvs_client.purge_all_asset_clips(self.asset_id)

def get_items(filepath):
    with open(filepath) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    return [x.strip() for x in content]

if __name__ == "__main__":
    lvs_username = os.environ['LVS_USERNAME']
    lvs_password = os.environ['LVS_PASSWORD']
    lvs_api_key = os.environ['LVS_API_KEY']
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--Input", help="Show Input")
    args = parser.parse_args()
    if args.Input:
        print("file path is : % s" % args.Input)
    else:
        print("Input is missing")

    asset_list = get_items(args.Input)
    delete_searchable_clips = DeleteSearchableClips(lvs_api_key, lvs_username, lvs_password)

    for item in asset_list:
        delete_searchable_clips.set_asset_id(item)
        result = delete_searchable_clips.start_deleting_searchable_clips()
        print(result)
