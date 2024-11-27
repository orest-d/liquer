from textual.app import App
from textual.widgets import DataTable, Footer, Header, Label, Static, TextArea
from textual import events
from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import VerticalGroup
from rich.text import Text

from liquer.parser import parse
from liquer.store import get_store, join_key, key_extension, key_name, parent_key
from textual.screen import Screen

class TUIApp(App):
    BINDINGS = [("Q", "exit", "Exit")]
    def compose(self):
        yield Header()
        yield KeyDisplay()
        yield StoreView()
        yield Message()
        yield Footer()

    def on_mount(self):
        self.query_one(StoreView).key=""
#        data_table = self.query_one(DataTable)
#        data_table.add_column("Column 1")
#        data_table.add_column("Column 2")
#        data_table.add_row("Row 1, Column 1", "Row 1, Column 2")
#        data_table.add_row("Row 2, Column 1", "Row 2, Column 2")

#    def on_key(self, event: events.Key):
#        if event.key == "q":
#            self.exit()
    def action_exit(self):
        self.exit()

def get_unicode_icon(metadata):
    try:
        if metadata["fileinfo"]["is_dir"]:
            return "📁"
    except:
        pass
    
    type_identifier = metadata.get("type_identifier")
    query=metadata.get("query")
    extension=None
    if query:
        extension=parse(query).extension()
    extension = extension or key_extension(metadata.get("key"))

    filename=None
    if query:
        filename=parse(query).filename()
    filename = filename or key_name(metadata.get("key"))

    if filename=="recipes.yaml":
        return "🍷"
    if type_identifier in ("dataframe", "polars_dataframe") or extension in ("csv", "tsv", "xlsx", "parquet"):
        return "🧮" #"𝄝"
    if extension in ("htm","html","rtf","doc","md","tex","pdf","docx"):        
        return "📰"
    if extension in ("png","jpg","jpeg","svg"):
        return "🎨"
    if extension in ("json","pkl","pickle","yaml"):
        return "💾"
    if extension in ("sql",):
        return "🐌"
    if extension in ("py",):
        return "🐍"
    if type_identifier in ("text",):
        return "📄"
    return "📦"   

def get_status(metadata):
    status=metadata.get("status")

    status={
        "none":"[blue]none[/]",
        "submitted":"[yellow]submitted[/]",
        "parent":"[yellow]parent[/]",
        "evaluation":"[yellow]evaluation[/]",
        "dependencies":"[yellow]dependencies[/]",
        "error":"[red]error[/]",
        "recipe":"[blue]recipe[/]",
        "ready":"[green]ready[/]",
        "expired":"[blue]expired[/]",
        "external":"[green]external[/]",
        "side-effect":"[green]side-effect[/]"}.get(status,status)
    return status or "[red]???[/]"

class TextView(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Return")]
    text=reactive("")
    head=reactive("")

    def __init__(self, text):
        super().__init__()
        self.text=text
    def compose(self):
        yield Label(self.text)
        yield Footer()
    def render(self):
        return Text(self.text)
    
class StoreView(VerticalGroup):
    key=reactive("")
    DEFAULT_CSS = """
    StoreView {
      layout: vertical;
      height: auto;
    }
    #table {
      height: 1fr;
    }
    #key {
      height: 1;
    }
    #message {
      height: 1;
    }
    """
    rows=[]
    def compose(self):
        yield KeyDisplay(id="key")
        yield DataTable(id="table")
        yield Message(id="message")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        row=int(event.cursor_row)
        if row:
            key=join_key(self.key, self.rows[row][2])
            metadata=get_store().get_metadata(key)
            try:
                if metadata["fileinfo"]["is_dir"]:
                    self.key=key
                    return
            except:
                pass
            try:
                text=get_store().get_bytes(key).decode("utf-8")
                self.app.push_screen(TextView(text))
            except:
                pass
        else:
            self.action_up()
    def on_mount(self):
        data_table = self.query_one(DataTable)
        data_table.add_column("Column 1")
        data_table.add_column("Column 2")
        data_table.add_row("Row 1, Column 1", "Row 1, Column 2")
        data_table.add_row("Row 2, Column 1", "Row 2, Column 2")
    
    def action_up(self):
        key=parent_key(self.key)
        self.key= "" if key is None else key

    def watch_key(self, old, new_key):
        self.query_one("#key").key=new_key

        table:DataTable=self.query_one("#table")
        table.cursor_type="row"
        table.clear(True)
        table.add_columns("I   ","state       ", "name                  ","title                                                  ")
        store=get_store()
        rows=[("📁", "", ".." if new_key else "", "")]
        for filename in store.listdir(new_key):
            key=join_key(new_key, filename)
            meta=store.get_metadata(key)
            icon = get_unicode_icon(meta)
            status = get_status(meta)

            rows.append((icon, status, filename, meta.get("title","")))
        self.rows=rows
        table.add_rows(rows)

            
class KeyDisplay(Widget):
    key = reactive("")
    def render(self):
        return f"Key: [b]{self.key}[/]"

class Message(Widget):
    message = reactive("")
    def render(self):
        return self.message


if __name__ == "__main__":
    TUIApp().run()
