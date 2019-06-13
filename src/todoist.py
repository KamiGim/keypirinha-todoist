# Keypirinha launcher (keypirinha.com)
import re
import os
import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet
from todoist.api import TodoistAPI


class Todoist(kp.Plugin):

    DEFAULT_ADD_TASK_LABEL = "atodoist"
    DEFAULT_DELETE_TASK_LABEL = "dtodoist"
    DEFAULT_TODO_PATH = os.environ['HOMEPATH']
    REGEX_INPUT = r'(\S+)\s(.+)'
    REGEX_TODO_TXT = r'(\d+)\.(.+)'
    REGEX_LABEL = r'(\w+) : (.+)'
    ITEM_EASYSEARCH = kp.ItemCategory.USER_BASE + 1
    DEFAULT_TOKEN = "ec040780698fb9ba22aca4f0ee8ed1ffc2fbbe6a"

    add_task_label = DEFAULT_ADD_TASK_LABEL
    todo_path = DEFAULT_TODO_PATH

    def __init__(self):
        super().__init__()

    def _read_config(self):

        settings = self.load_settings()
        self.add_task_label = settings.get_stripped("add_task_label", "main", self.DEFAULT_ADD_TASK_LABEL)
        self.delete_task_label = settings.get_stripped("delete_task_label", "main", self.DEFAULT_DELETE_TASK_LABEL)
        self.todo_path = os.path.abspath(settings.get_stripped("todo_path", "main", self.DEFAULT_TODO_PATH))
        self.todo_path = os.path.join(settings.get_stripped("todo_path", "main", self.DEFAULT_TODO_PATH), 'todo.txt')
        self.user_token = settings.get_stripped("user_token", "main", self.DEFAULT_TOKEN)
        self.api = TodoistAPI(self.user_token)
        self.api.sync()

    def on_start(self):
        self.dbg("On Start")
        self._read_config()


    def on_catalog(self):
        pass

    def on_suggest(self, user_input, items_chain):
        input = re.search(self.REGEX_INPUT, user_input)
        suggestions = []

        if input is None:
            return None

        if self.add_task_label == input.group(1) and len(input.groups()) == 2:

            term = input.group(2)

            target = term.strip().format(q = term.strip())

            suggest_label = self.add_task_label + ' : ' + term + ' to your todo.txt.'

            suggestions.append(self.create_item(
                category=self.ITEM_EASYSEARCH,
                label = suggest_label,
                short_desc=target,
                target=target,
                args_hint = kp.ItemArgsHint.FORBIDDEN,
                hit_hint = kp.ItemHitHint.IGNORE,
                loop_on_suggest = True
            ))
            self.set_suggestions(suggestions, kp.Match.DEFAULT, kp.Sort.NONE)

        if self.delete_task_label == input.group(1) and len(input.groups()) == 2:
            term = input.group(2)
            term.isdigit()
            if term.isdigit() and int(term) != 0:
                suggest_label = self.delete_task_label + ' : delete ' + term + ' task from your todo.txt.'
                suggestions.append(self.create_item(
                    category=self.ITEM_EASYSEARCH,
                    label = suggest_label,
                    short_desc=term,
                    target=term,
                    args_hint = kp.ItemArgsHint.FORBIDDEN,
                    hit_hint = kp.ItemHitHint.IGNORE,
                    loop_on_suggest = True
                ))
                self.set_suggestions(suggestions, kp.Match.DEFAULT, kp.Sort.NONE)

    def on_execute(self, item, action):
        label = re.search(self.REGEX_LABEL, item.label())
        action = label.group(1);
        target = item.target()
        print(self.api)

        if action == self.add_task_label:
            item = self.api.items.add(target)
            self.api.commit()

        if action == self.delete_task_label:
            with open(self.todo_path, "r") as f:
                lines = f.readlines()
                with open(self.todo_path, "w") as f:
                    count = 1
                    for line in lines:
                        if count < int(target):
                            f.write(line)
                        if count > int(target):
                            text = re.search(self.REGEX_TODO_TXT, line)
                            f.write(str(count - 1) + '.' + text.group(2) + "\n")
                        count += 1

    def on_activated(self):
        pass

    def on_deactivated(self):
        pass

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self.on_start()

    def _set_action(self, name, label, desc):
        return self.create_action(
        name = name,
        label = label,
        short_desc = desc
        )
