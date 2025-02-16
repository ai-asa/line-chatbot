# %%
from src.line.richmenu_controller import RichmenuController

if __name__ == "__main__":
    rt = RichmenuController()
    # rt.get_rich_menu_list()
    # rt.change_richmenu_default(1)
    # rt.cancel_richmenu_default()
    # rt.delete_all_richmenus_and_aliases()
    # imagepath_list = ["./data/richmenu/images/機能選択画面v3.png","./data/richmenu/images/契約画面v3.png"]
    # rt.gen_richmenu(imagepath_list)
    rt.change_richmenu_default(1,"richmenu-ab1b74660e35e87b457cde77df8549f2")
    rt.get_default_richmenu()
    rt.get_richmenu_alias("richmenu-alias-a","richmenu-ab1b74660e35e87b457cde77df8549f2")
    rt.get_richmenu_alias("richmenu-alias-b","richmenu-db51ad0feaecb6e1334ecf2e4e3d0f52")


# %%
