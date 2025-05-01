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
    rt.change_richmenu_default(1,"richmenu-e7f9145bc89967c78772e1b5c815252d")
    rt.get_default_richmenu()
    rt.get_richmenu_alias("richmenu-alias-a","richmenu-e7f9145bc89967c78772e1b5c815252d")
    rt.get_richmenu_alias("richmenu-alias-b","richmenu-732ee97a58fce1ca347e217efe731702")


# %%
