# %%
from src.line.richmenu_controller import RichmenuController

if __name__ == "__main__":
    rt = RichmenuController()
    # rt.get_rich_menu_list()
    # rt.change_richmenu_default(1)
    # rt.cancel_richmenu_default()
    # rt.delete_all_richmenus_and_aliases()
    # imagepath_list = ["./data/richmenu/images/リッチメニュー_準備中v1.png","./data/richmenu/images/リッチメニュー_準備中v2.png"]
    # rt.gen_richmenu(imagepath_list)
    rt.change_richmenu_default(1,"richmenu-6bf32ec02a0d404abac4c7f62010ae26")
    rt.get_default_richmenu()
    rt.get_richmenu_alias("richmenu-alias-a","richmenu-6bf32ec02a0d404abac4c7f62010ae26")
    rt.get_richmenu_alias("richmenu-alias-b","richmenu-ddeccbf6ed74440023f19998985d6d3a")


# %%
