#!/usr/bin/env python3

import sys
import textwrap
from enum import Enum
from typing import List

###############################################################################
#                              CONSOLE UTILITIES                              #
###############################################################################

class StatusColors(str, Enum):
    """A Enum for colors using ANSI escape sequences.
    Referece: 
    - https://stackoverflow.com/questions/287871
    """

    OK = "\033[92m"
    INFO = "\033[94m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"

class Level(str, Enum):
    """A Enum for message levels .
    """

    OK = "OK"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

def linter_text_padding(text: str, width: int=72, 
                 side: bool=True, symbol: str=" ") -> str:
    """
    Returns a string with the text padded with spaces on the left or right.
    text: The text to pad.
    width: The width to pad to.
    side: True for left, False for right.
    symbol: The symbol to pad with.
    """
    if not side:
        return f"{symbol * (width - len(text))}{text}"
    
    return f"{text}{symbol * (width - len(text))}"

def linter_message(message: str, level: Level) -> str:
    """Returns a message with appropriate policy colors and line wrapping."""
    
    policy_message = StatusColors[level] \
        + StatusColors.BOLD \
        + f"{level}: " \
        + message \
        + StatusColors.ENDC

    return textwrap.fill(
        policy_message, width=72, subsequent_indent="        "
    )

###############################################################################
#                            COMMIT TRANSFORMER                               #
###############################################################################
def get_commit_message(msg_temp_file, keep_comments=False) -> List[str]:
    """Returns the commit message as a list of lines from the temporary file"""
    commit_message = None
    with open(msg_temp_file, "r", encoding="utf-8") as f_msg:
        commit_message = f_msg.readlines()
    
    if not keep_comments:
        commit_message = [
            line 
            for line in commit_message 
            if not line.strip().startswith("#")
        ]
    
    return commit_message

###############################################################################
#                                 Validators                                  #
###############################################################################
def has_title_and_body(commit_message: List[str]) -> tuple:
    """Returns (True, None) if the commit message has a title and body."""
    return (len(commit_message) >= 4,None)


def title_within_max_length(commit_message: List[str]) -> tuple:
    """Returns (True, None) if the title is within the maximum length.
    Returns (False, max_length) if a line is too long."""
    max_length = 50
    title = commit_message[0]
    if len(title) > max_length:
        return (False, max_length)
    return (True, None)

def has_title_body_separator(commit_message: List[str]) -> tuple:
    """
    When title and body are separated by a blank line.
    Returns: (True, None)
    Status: True
    Hint: Not Provided

    When there is no blank line between title and body.
    Returns: (False, line_number)
    Status: False
    Hint: Not Provided
    """
    return (commit_message[1].strip() == "", None)

def has_trailing_line(commit_message: List[str]) -> tuple:
    """
    When there is a trailing line at the end of the commit message.
    Returns: (True, None)
    Status: True
    Hint: Not Provided

    When there is no trailing line at the end of the commit message.
    Returns: (False, line_number)
    Status: False
    Hint: Not Provided
    """
    return (commit_message[-1].strip() == "", None)

def body_within_max_length(commit_message: List[str]) -> tuple:
    """Returns (True, None) if the body is within the maximum length.
    Returns (False, line_number) if a line is too long."""
    # exclude the title and the separator and the trailing line
    body = commit_message[2:-1]
    
    for line_number, line in enumerate(body, start=1):
        if len(line) > 72:
            return (False, line_number)

    return (True, None)

def title_starts_with_commit_type(commit_message: List[str]) -> tuple:
    """
    When the title starts with the commit type.
    Returns: (True, None)
    Status: True
    Hint: Not Provided

    When the title does not start with the commit type.
    Returns: (False, List[Valid Commit Types])
    Status: False
    Hint: List of valid commit types
    """
    valid_commit_types = ["feat", "fix", "refactor", "style", 
                          "docs", "test", "chore", "revert"]
    
    title = commit_message[0]
    for commit_type in valid_commit_types:
        if title.startswith(f"{commit_type}:"):
            return (True, None)
    
    return (False, valid_commit_types)

def commit_type_require_issue_number(commit_message: List[str]) -> tuple:
    """Returns (True, None) if the commit type requires an issue number.
    Returns (False, None) if the commit type does not require an issue number.
    """
    title = commit_message[0]
    if title.startswith("feat:") or title.startswith("fix:"):
        return (True, None)
    return (False, None)

# Detailed Checks
def title_has_issue_number(commit_message: List[str]) -> tuple:
    """
    When an issue tracker handle has been found followed by an issue number.
    Returns: (True, None)
    Status: True
    Hint: Not Provided

    When an issue tracker handle hasn't been found
    Returns: (False, List[(IssueTrackerHandle, IssueTrackerLongName),...])
    Status: False
    Hint: List of Issue Tracker Handles with Long Names

    When an isue tracker handle has been found but no issue number
    Returns: (False,(None, False))
    Status: False
    Hint: None to indicate Issue Tracker is correct 
          False to indicate no issue number
    """
    title = commit_message[0]
    valid_issue_tracker_prefixes = [('jr:', 'jira'), ('gh:', 'github'),
                                    ('gl:', 'gitlab'),('bb:', 'bitbucket'),
                                    ('lp:', 'launchpad')]
    for issue_tracker, _ in valid_issue_tracker_prefixes:
        if issue_tracker in title:
            # get the issue number from the title
            issue_number = title.split(issue_tracker)[1].split()[0]
            if issue_number.isdigit():
                return (True, None)
            else:
                return (False, (None, False))
    
    return (False, valid_issue_tracker_prefixes)

###############################################################################
#                                LINTER                                       #
###############################################################################
def lint_commit_message():
    """The main function of the commit-msg hook."""
    commit_message = get_commit_message(sys.argv[1], keep_comments=False)

    flag, hint = has_title_and_body(commit_message)
    if not flag:
        print(
            linter_message(
                "Title and Body are required",
                Level.ERROR
            )
        )
        return 1
    else:
        print(
            linter_message(
                "Commit Message has a title and body.", Level.OK
            )
        )

    flag, hint = title_within_max_length(commit_message)
    if not flag:
        print(linter_message("Title is too long:", Level.ERROR), 
              linter_message(f"Max Length: {hint}", Level.INFO))
        return 1
    else:
        print(
            linter_message(
                "Title is within the maximum length.", Level.OK
            )
        )

    flag, hint = has_title_body_separator(commit_message)
    if not flag:
        print(
            linter_message(
                "A blank line is required between the title and body",
                Level.ERROR
            )
        )
        return 1
    else:
        print(
            linter_message(
                "Commit Message has a blank line between title and body.",
                Level.OK
            )
        )

    flag, hint = has_trailing_line(commit_message)
    if not flag:
        print(
            linter_message(
                "A blank line is required at the end of the commit message",
                Level.ERROR
            )
        )
        return 1
    else:
        print(
            linter_message(
                "Commit message has a trailing line.",
                Level.OK
            )
        )
    
    flag, hint = body_within_max_length(commit_message)
    if not flag:
        print(
            linter_message(
                "Commit Body lines are too long:",
                Level.ERROR
            ),
            linter_message(
                f"Line {hint}",
                Level.INFO
            )
        )
        return 1
    else:
        print(
            linter_message(
                "Commit Body lines are within the maximum length.",
                Level.OK
            )
        )
    
    flag, hint = title_starts_with_commit_type(commit_message)
    if not flag:
        print(
            linter_message(
                "Title must start with a valid commit type", 
                Level.ERROR
            ),
            "\n",
            linter_message(
                f"Valid Commit Types: {hint}",
                Level.INFO
            )
        )
        return 1
    else:
        print(
            linter_message(
                "Title starts with a valid commit type.",
                Level.OK
            )
        )

    flag, hint = commit_type_require_issue_number(commit_message)
    if flag is False:
                print(
            linter_message(
                "Commit type does not require an issue number.",
                Level.INFO
            )
        )
    else:
        print(
            linter_message(
                "Commit type requires an issue number checking.....",
                Level.INFO
            )
        )

        flag, hint = title_has_issue_number(commit_message)
        # there is an issue number in the title
        if not flag:
            # check if the issue tracker is valid
            if type(hint) is list:
                message_hint = \
                    linter_message(
                        "Issue Tracker is not valid.",
                        Level.ERROR
                    ) + \
                    "\n"
            elif type(hint) is tuple:
                message_hint = \
                    linter_message(
                        "Issue Tracker is valid but no issue number provided.",
                        Level.ERROR
                    ) + \
                    "\n"
                
            # get hints for valid issue trackers
            tracker_hints = ""
            for handle, name in hint:
                issue_tracker_hint = f"for {name} -> {handle}:123"
                tracker_hints += linter_text_padding(
                    text=issue_tracker_hint
                )
            # build the message hint
            message_hint += linter_message(
                linter_text_padding("List of Valid Issue Trackers e.g:")
                + tracker_hints,
                Level.INFO
            )

            print(message_hint)
            return 1
        else:
            print(
                linter_message(
                    "Commit Message has a valid issue number.",
                    Level.OK
                )
            )

    return 0


def main():
    print("commit-msg hook was called")

if __name__ == '__main__':
    main = lint_commit_message
    sys.exit(main())