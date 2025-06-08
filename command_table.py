import tape_command_table
import floppy_command_table


class CommandTable:

    def set(tableType):
        print("using table", tableType)
        if tableType == "tape":
            CommandTable.COMMAND = tape_command_table.COMMAND
            CommandTable.FUNCTION = tape_command_table.FUNCTION
        elif tableType == "floppy":
            CommandTable.COMMAND = floppy_command_table.COMMAND
            CommandTable.FUNCTION = floppy_command_table.FUNCTION
        else:
            raise Exception("Unknown command table type", tableType)

        CommandTable.COMMAND_BY_WORD = {
            v: k for k, v in CommandTable.COMMAND.items()}
        CommandTable.FUNCTION_BY_WORD = {
            v: k for k, v in CommandTable.FUNCTION.items()}


CommandTable.set("tape")
