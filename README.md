#Set up virtual environment by following commands.

python3 -m pip install --user virtualenv

python3 -m venv env

source env/bin/activate

python3 -m pip install -r requirements.txt


#Run following command to delete the asset id from terminal

LVS_USERNAME=<lvs_user_name> LVS_PASSWORD=<lvs_password> LVS_API_KEY=<lvs_api_key> python3 lvs_api/delete_searchable_clips.py -i <file_path_with_asset_ids>

# in the input file each asset must be in separate line

#Deactivate the terminal environment by below command
deactivate 
