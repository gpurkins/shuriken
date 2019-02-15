import datetime
import sys
import argparse
import errno
import os
from splinter import Browser



class Color:
    # Use colors to make command line output prettier
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


class Shuriken:

    def __init__(self):
        # Expect some weird characters from fuzz lists, make encoding UTF-8
        reload(sys)
        sys.setdefaultencoding('utf8')

        # All potential XSS findings
        self.xss_links = []

        # Get user args and store
        self.user_args = self.parse_args()

        # PhantomJS browser 
        self.browser = Browser('chrome', headless=True)

    def make_sure_path_exists(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def inject_payload(self, payload, link, screenshot_target):
        # visit user supplied link with injected payload
        browser = self.browser

        # Let user specify where in the URL fuzz values should be injected
        injected_link = link.replace("{xss}", payload)

        browser.visit(injected_link)
        try:
            alert = browser.get_alert()
            alert.dismiss()
        except:
            pass        
        

        # Keep index of screens, so they can be easily
        # linked to line nums in log
        self.screen_index = str(len(self.xss_links) + 1)

        # Check to see if payload was reflected in HTML source
        if payload in browser.html:
            print Color.GREEN + "\nPotential XSS vulnerability found:" + \
                Color.END
            # If user set the --screen flag to target, capture screen of
            # payload
            if screenshot_target is not None:
                # Check if screenshots directory exists, if not then create it
                self.make_sure_path_exists("screenshots")
                screenshot_file_name = "screenshots/" + \
                    screenshot_target + "_" + \
                    datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + \
                    "_" + self.screen_index + ".png"
                # Save screenshot to directory
                browser.driver.save_screenshot(screenshot_file_name)
                print Color.YELLOW + "Screenshot saved: " + \
                    screenshot_file_name + Color.END
            # Add link to list of all positive XSS hits
            self.xss_links.append(injected_link)
            return Color.BLUE + injected_link + Color.END
        else:
            return Color.YELLOW + "\nTested, but no XSS found at: \n" + \
                Color.RED + injected_link + Color.END

    def test_xss(self, payloads_param, link, screenshot_target):
        # Load the payload file and inject all payloads
        # into user supplied URL to test for XSS
        payloads = []
        with open(payloads_param) as file:
            for line in file:
                line = line.strip()
                payloads.append(line)
        for item in payloads:
            print self.inject_payload(item, link, screenshot_target)

    def log_file(self, link_list):
        # Prompt the user to confirm log file, if yes, log XSS hits
        log_confirm = raw_input(
            "\nWould you like to save these results? [y/n] > ")
        if log_confirm == "y":
            target_name = raw_input("Please enter the target name > ")
            # Check if logs directory exists, if not then create it
            self.make_sure_path_exists("logs")
            # Save log file to directory
            file_name = "logs/" + target_name + "_" + \
                datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + \
                ".txt"
            with open(file_name, 'w') as file:
                for link in link_list:
                    file.write(link)
                    file.write("\n")
                # Add metadata about what payload file was used
                file.write("\n*** Created from the payload file >>> " +
                           self.user_args.PAYLOADS_LIST)
                file.close()
            print "\nFile successfully saved as: " + \
                Color.BLUE + file_name + Color.END
            print "\n"
        else:
            print "\nGoodbye!"
            print "\n"

    def parse_args(self):
        # Parse arguments from the user sent on command line
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-u', action='store', dest='URL',
            help='The URL to analyze', required=True)
        parser.add_argument(
            '-p', action='store', dest='PAYLOADS_LIST',
            help='The payload list to use', required=True)
        parser.add_argument(
            '--screen', action='store', dest='SCREENSHOT_NAME',
            help='Screens of target')

        arguments = parser.parse_args()

        # Check for existence of {xss} injection point in URL string
        if "{xss}" not in arguments.URL:
            print Color.RED + "Please provide the '{xss}' placeholder for" + \
                " injection point in the URL" + Color.END
            print Color.GREEN + \
                "Example: -u \"http://example.com/index.php?name={xss}\"" + \
                Color.END
            exit()

        return arguments

    def main(self):
        # Print out a welcome message
        print "\n"
        print "=" * 34 + Color.YELLOW + "\nWelcome to the" + Color.RED + \
            " Shuriken " + Color.YELLOW + "XSS tool!\n" + \
            Color.END + "=" * 34 + "\n"

        try:
            self.test_xss(self.user_args.PAYLOADS_LIST,
                          self.user_args.URL, self.user_args.SCREENSHOT_NAME)
            print Color.GREEN + "\n=== Testing complete! ===\n" + Color.END

            # If the test found possible XSS vulnerabilities, ask if we should
            # log
            if self.xss_links:
                print Color.YELLOW + \
                    "Potential XSS vulnerabilities were detected!" + \
                    Color.END
                self.log_file(self.xss_links)
            else:
                print Color.YELLOW + \
                    "No potential XSS vulnerabilities detected...\n" + \
                    Color.END
                print "Goodbye!"
                print "\n"
        except KeyboardInterrupt:
            print Color.YELLOW + \
                "\nTesting interrupted by user!\n" + Color.END
            self.log_file(self.xss_links)
            sys.exit()


if __name__ == "__main__":
    Shuriken().main()
