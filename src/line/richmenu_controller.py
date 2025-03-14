# %%
import os
from dotenv import load_dotenv
import configparser
import requests
import json

class RichmenuController:
    load_dotenv()
    LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
    config = configparser.ConfigParser()
    config.read('config.txt')
    richMenuIds_path = config.get('DATA', 'richmenu_ids_path', fallback="./data/richmenu/ids/ids.json")
    rich_Image_path = config.get('DATA', 'richmenu_image_path', fallback="./data/richmenu/images/")

    def __init__(self):
        if not os.path.exists(self.richMenuIds_path):
            self.gen_richmenu()
        with open(self.richMenuIds_path,'r') as f:
            self.richMenuIds = json.load(f)
        pass

# タブ選択：240*843 240*843
# 空白：160*1686
# 両脇空白：100、左上


#
    def gen_richmenu(self,image_path_list):
        data_list = []
        data_1= {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": False,
            "name": "functionTab",
            "chatBarText": "Menu",
            "areas": [
                {
                    "bounds": {
                        "x": 1251,
                        "y": 0,
                        "width": 1250,
                        "height": 240
                    },
                    "action": {
                        "type": "richmenuswitch",
                        "richMenuAliasId": "richmenu-alias-b",
                        "data": "tab"
                    }
                },
                {
                    "bounds": {
                        "x": 100,
                        "y": 490,
                        "width": 720,
                        "height": 475
                    },
                    "action": {
                        "type": "postback",
                        "data": "kn"
                    }
                },
                {
                    "bounds": {
                        "x": 900,
                        "y": 490,
                        "width": 720,
                        "height": 475
                    },
                    "action": {
                        "type": "postback",
                        "data": "gs"
                    }
                },
                {
                    "bounds": {
                        "x": 1695,
                        "y": 490,
                        "width": 720,
                        "height": 475
                    },
                    "action": {
                        "type": "postback",
                        "data": "qa"
                    }
                },
                {
                    "bounds": {
                        "x": 100,
                        "y": 1060,
                        "width": 720,
                        "height": 475
                    },
                    "action": {
                        "type": "postback",
                        "data": "yo"
                    }
                },
                {
                    "bounds": {
                        "x": 900,
                        "y": 1350,
                        "width": 740,
                        "height": 190
                    },
                    "action": {
                        "type": "postback",
                        "data": "rps"
                    }
                },
                {
                    "bounds": {
                        "x": 1650,
                        "y": 1350,
                        "width": 740,
                        "height": 190
                    },
                    "action": {
                        "type": "postback",
                        "data": "rpr"
                    }
                },
            ]
        }
        data_list.append(data_1)
        data_2= {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": False,
            "name": "functionTab",
            "chatBarText": "Menu",
            "areas": [
                {
                    "bounds": {
                        "x": 0,
                        "y": 0,
                        "width": 1250,
                        "height": 240
                    },
                    "action": {
                        "type": "richmenuswitch",
                        "richMenuAliasId": "richmenu-alias-a",
                        "data": "tab"
                    }
                },
                {
                    "bounds": {
                        "x": 100,
                        "y": 450,
                        "width": 720,
                        "height": 1120
                    },
                    "action": {
                        "type": "postback",
                        "data": "try"
                    }
                },
                {
                    "bounds": {
                        "x": 880,
                        "y": 450,
                        "width": 740,
                        "height": 510
                    },
                    "action": {
                        "type": "postback",
                        "data": "980"
                    }
                },
                {
                    "bounds": {
                        "x": 1655,
                        "y": 450,
                        "width": 740,
                        "height": 510
                    },
                    "action": {
                        "type": "postback",
                        "data": "1980"
                    }
                },
                {
                    "bounds": {
                        "x": 880,
                        "y": 1060,
                        "width": 740,
                        "height": 510
                    },
                    "action": {
                        "type": "postback",
                        "data": "XXX"
                    }
                },
                {
                    "bounds": {
                        "x": 1665,
                        "y": 1060,
                        "width": 740,
                        "height": 510
                    },
                    "action": {
                        "type": "postback",
                        "data": "free"
                    }
                },
            ]
        }
        data_list.append(data_2)
        parts = []
        for i in range(len(data_list)):
            richmenu_id = self._gen_richmenu(data_list[i],image_path_list[i])
            part = {
                "richMenu_Num":i+1,
                "richMenu_Id":richmenu_id
            }
            parts.append(part)
        with open(self.richMenuIds_path, 'w') as f:
            json.dump(parts, f)
        pass

    def _gen_richmenu(self,data,image_path):
        headers = {
            'Authorization': f'Bearer {self.LINE_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        response = requests.post('https://api.line.me/v2/bot/richmenu', 
                                 headers=headers, 
                                 data=json.dumps(data))
        response_json = response.json()
        print(response_json)
        richmenu_id = response_json.get("richMenuId")
        self._upload_image(richmenu_id,image_path)
        return richmenu_id

    def _upload_image(self,richmenu_id,image_path):
        headers = {
            'Authorization': f'Bearer {self.LINE_ACCESS_TOKEN}',
            'Content-Type': 'image/png'
        }
        with open(image_path, 'rb') as f:
            response = requests.post(f'https://api-data.line.me/v2/bot/richmenu/{richmenu_id}/content', 
                                     headers=headers, 
                                     data=f)
            print(response.status_code, response.reason)
            print(response.text)

    def change_richmenu_user(self,rich_num,user_id):
        for richMenuId in self.richMenuIds:
            if richMenuId["richMenu_Num"] == rich_num:
                rich_id = richMenuId["richMenu_Id"]
        try:
            response = requests.post(f'https://api.line.me/v2/bot/user/{user_id}/richmenu/{rich_id}', 
                                    headers={'Authorization': f'Bearer {self.LINE_ACCESS_TOKEN}'})
            print(response.status_code, response.reason)
            print(response.text)
        except:
            print("richMenuIdが見つかりません。")
        pass

    def change_richmenu_default(self,rich_num,richmenuId=""):
        if not richmenuId:
            for richMenuId in self.richMenuIds:
                if richMenuId["richMenu_Num"] == rich_num:
                    rich_id = richMenuId["richMenu_Id"]
        else:
            rich_id = richmenuId
        try:
            response = requests.post(f'https://api.line.me/v2/bot/user/all/richmenu/{rich_id}', 
                                    headers={'Authorization': f'Bearer {self.LINE_ACCESS_TOKEN}'})
            print(response.status_code, response.reason)
            print(response.text)
        except:
            print("richMenuIdが見つかりません。")
        pass

    def cancel_richmenu_default(self):
        url = "https://api.line.me/v2/bot/user/all/richmenu"
        headers = {
            "Authorization": f"Bearer {self.LINE_ACCESS_TOKEN}"
        }
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            print(f"Default rich menu cancelled successfully. Status code: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while cancelling default rich menu: {e}")
            return False

    def get_richmenu_alias(self,aliasId,richMenuId):
        url = "https://api.line.me/v2/bot/richmenu/alias"
        headers = {
            "Authorization": f"Bearer {self.LINE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "richMenuAliasId": aliasId,
            "richMenuId": richMenuId
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            print(f"Rich menu alias created successfully. Status code: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while creating rich menu alias: {e}")
            return False

    def get_rich_menu_list(self):
        url = "https://api.line.me/v2/bot/richmenu/list"
        headers = {
            "Authorization": f"Bearer {self.LINE_ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            rich_menus = response.json()["richmenus"]
            for menu in rich_menus:
                print(f"Rich Menu ID: {menu['richMenuId']}")
                print(f"Name: {menu['name']}")
                print("---")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    def get_default_richmenu(self):
        url = "https://api.line.me/v2/bot/user/all/richmenu"
        headers = {
            "Authorization": f"Bearer {self.LINE_ACCESS_TOKEN}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            
            if response.status_code == 200:
                rich_menu_id = response.json().get("richMenuId")
                if rich_menu_id:
                    print(f"Default Rich Menu ID: {rich_menu_id}")
                    return rich_menu_id
                else:
                    print("No default rich menu is set.")
                    return None
            else:
                print(f"Unexpected status code: {response.status_code}")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while getting default rich menu: {e}")
            return None
        
    def get_richmenu_detail(self, rich_menu_id):
        url = f"https://api.line.me/v2/bot/richmenu/{rich_menu_id}"
        headers = {
            "Authorization": f"Bearer {self.LINE_ACCESS_TOKEN}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            if response.status_code == 200:
                rich_menu_detail = response.json()
                print(json.dumps(rich_menu_detail, indent=2))
                return rich_menu_detail
            else:
                print(f"Unexpected status code: {response.status_code}")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while getting rich menu detail: {e}")
            return None

    def delete_all_richmenus_and_aliases(self):
        # リッチメニューエイリアスの削除
        def delete_richmenu_aliases():
            url = "https://api.line.me/v2/bot/richmenu/alias/list"
            headers = {"Authorization": f"Bearer {self.LINE_ACCESS_TOKEN}"}
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                aliases = response.json().get("aliases", [])
                
                for alias in aliases:
                    alias_id = alias["richMenuAliasId"]
                    delete_url = f"https://api.line.me/v2/bot/richmenu/alias/{alias_id}"
                    delete_response = requests.delete(delete_url, headers=headers)
                    delete_response.raise_for_status()
                    print(f"Deleted rich menu alias: {alias_id}")
                
                return True
            except requests.exceptions.RequestException as e:
                print(f"Error occurred while deleting rich menu aliases: {e}")
                return False

        # リッチメニューの削除
        def delete_richmenus():
            url = "https://api.line.me/v2/bot/richmenu/list"
            headers = {"Authorization": f"Bearer {self.LINE_ACCESS_TOKEN}"}
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                richmenus = response.json().get("richmenus", [])
                
                for menu in richmenus:
                    menu_id = menu["richMenuId"]
                    delete_url = f"https://api.line.me/v2/bot/richmenu/{menu_id}"
                    delete_response = requests.delete(delete_url, headers=headers)
                    delete_response.raise_for_status()
                    print(f"Deleted rich menu: {menu_id}")
                
                return True
            except requests.exceptions.RequestException as e:
                print(f"Error occurred while deleting rich menus: {e}")
                return False

        # まずエイリアスを削除し、その後リッチメニューを削除
        aliases_deleted = delete_richmenu_aliases()
        menus_deleted = delete_richmenus()

        if aliases_deleted and menus_deleted:
            print("All rich menu aliases and rich menus have been successfully deleted.")
            return True
        else:
            print("There was an error deleting some or all rich menu aliases or rich menus.")
            return False

if __name__ == "__main__":
    rt = RichmenuController()
    rt.gen_richmenu()
    rt.change_richmenu_default(1)
    

# %%
