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
    rt.change_richmenu_default(1,"richmenu-e5d1166474227499f1a9a5244f7eb3b9")
    rt.get_default_richmenu()
    rt.get_richmenu_alias("richmenu-alias-a","richmenu-e5d1166474227499f1a9a5244f7eb3b9")
    rt.get_richmenu_alias("richmenu-alias-b","richmenu-a8e4d815bb0ec951068d253e09370814")


# %%
