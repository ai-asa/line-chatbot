# %%
from src.line.richmenu_controller import RichmenuController

if __name__ == "__main__":
    rt = RichmenuController()
    # rt.get_rich_menu_list()
    # rt.change_richmenu_default(1)
    # rt.cancel_richmenu_default()
    # rt.delete_all_richmenus_and_aliases()
    # imagepath_list = ["./data/richmenu/images/リッチメニュー_ファイナルv1.png","./data/richmenu/images/リッチメニュー_ファイナルv2.png"]
    # rt.gen_richmenu(imagepath_list)
    rt.change_richmenu_default(1,"richmenu-5631d916afd59291443bea36844af3a0")
    rt.get_default_richmenu()
    rt.get_richmenu_alias("richmenu-alias-a","richmenu-5631d916afd59291443bea36844af3a0")
    rt.get_richmenu_alias("richmenu-alias-b","richmenu-f3bdd9290c95af7d81004c3ab6a33157")


# %%
