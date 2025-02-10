# %%
from src.line.richmenu_controller import RichmenuController

if __name__ == "__main__":
    rt = RichmenuController()
    # rt.get_rich_menu_list()
    # rt.change_richmenu_default(1)
    # rt.cancel_richmenu_default()
    # rt.delete_all_richmenus_and_aliases()
    # imagepath_list = ["./data/richmenu/images/機能選択画面.png","./data/richmenu/images/契約画面.png"]
    # rt.gen_richmenu(imagepath_list)
    rt.change_richmenu_default(1,"richmenu-fca29072b5a45248510b309c7d91a4de")
    rt.get_default_richmenu()
    rt.get_richmenu_alias("richmenu-alias-a","richmenu-fca29072b5a45248510b309c7d91a4de")
    rt.get_richmenu_alias("richmenu-alias-b","richmenu-05cc77263a531c6d773d845fda05466d")


# %%
