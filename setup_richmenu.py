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
    rt.change_richmenu_default(1,"richmenu-9e5c3697a9eaa11e73728a3f2c592829")
    rt.get_default_richmenu()
    rt.get_richmenu_alias("richmenu-alias-a","richmenu-9e5c3697a9eaa11e73728a3f2c592829")
    rt.get_richmenu_alias("richmenu-alias-b","richmenu-75b3e40b87858e1fbeb9dcba61c82d32")


# %%
