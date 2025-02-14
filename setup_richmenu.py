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
    rt.change_richmenu_default(1,"richmenu-2638d235c437db8d60690fdb75133ae2")
    rt.get_default_richmenu()
    rt.get_richmenu_alias("richmenu-alias-a","richmenu-2638d235c437db8d60690fdb75133ae2")
    rt.get_richmenu_alias("richmenu-alias-b","richmenu-83adfd9fcfa159fd772cbebdb09f7cfe")


# %%
