import asyncio, sys, traceback, urllib3
from docopt import docopt, DocoptExit
from . import AGENT
from .client import mt_endpoints, CxOneClientFactory
from .convert import (
    ConversionException,
    AbortedConversionException,
)
from .commands import command_map


async def main():
    # fmt: off
    """Usage:
    cxone-repo-tools (-h | --help | --version) [<command>]
    cxone-repo-tools --tenant TENANT (--cxone-hostname FQDN | --cxone-region REGION)
      (--api-key APIKEY | --api-key-env)
      [--threads THREADS]
      [--retries RETRIES]
      [-k] [--proxy-url PROXY_URL]
      <command> [<args>...]
    cxone-repo-tools --tenant TENANT (--cxone-hostname FQDN | --cxone-region REGION)
      --client-id CLIENTID (--client-secret SECRET | --client-secret-env)
      [--threads THREADS]
      [--retries RETRIES]
      [-k] [--proxy-url PROXY_URL]
      <command> [<args>...]
      
    -h, --help                     Display help and exit

    --version                     Display version and exit

    
    ## Connection Options

    Define the connection to Checkmarx One.

    --tenant TENANT               Checkmarx One tenant

    --api-key APIKEY              Checkmarx One API Key

    --api-key-env                 Obtain the API Key from environment variable CX_API_KEY

    --client-id CLIENTID          Checkmarx One OAuth Client ID

    --client-secret SECRET        Checkmarx One OAuth Client Secret

    --client-secret-env           Obtain the OAuth client secret from environment variable CX_CLIENT_SECRET

    --cxone-hostname FQDN         The FQDN of the CxOne hostname for your instance
                                  (name only, not the https:// protocol prefix)

    --cxone-region REGION         The multi-tenant region: {MTREGION}

    ## Operation Options

    --retries RETRIES             The number of retries to attempt with API failures. [default: 255]

    -k                            Turn off SSL verification

    --proxy-url PROXY_URL         URL to proxy server
    
    --threads THREADS             The number of concurrent threads. [default: 2]

    ## Available Commands

    ### SCM Connection Management

    export-projects               Export a list of projects connected to an SCM.
    export-scms                   Export a list of the configured SCMs.
    convert-scms                  Convert one or more projects to use a different SCM.
    connect-scm                   Connect a non-connected project to an SCM.
    disconnect-scm                Disconnect a project from the connected SCM.

    ### SCA Private Package Repository Configurations


    """
    # fmt: on

    try:
        args = docopt(
            main.__doc__.replace("{MTREGION}", mt_endpoints()),
            version=AGENT,
            options_first=True,
            default_help=False,
        )

        if (args["--help"] or args["-h"]) and args["<command>"] is None:
            print(main.__doc__)
            exit(0)
        elif (
            (args["--help"] or args["-h"])
            and args["<command>"] is not None
            and args["<command>"] in command_map.keys()
        ):
            command_map[args["<command>"]].print_help()
            exit(0)

        if bool(args["-k"]):
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        client = CxOneClientFactory.client_factory(
            args["--api-key"],
            args["--api-key-env"],
            args["--client-id"],
            args["--client-secret"],
            args["--client-secret-env"],
            args["--cxone-hostname"],
            args["--cxone-region"],
            args["--tenant"],
            args["--proxy-url"],
            not bool(args["-k"]),
            int(args["--retries"]),
        )

        threads = int(args["--threads"])

        if args["<command>"] in command_map.keys():
            await command_map[args["<command>"]](client, threads, AGENT).execute(
                args["<args>"]
            )
        else:
            print(f"{args['<command>']} is unknown.")
            exit(1)

        exit(0)
    except DocoptExit as bad_args:
        print("Incorrect arguments provided.", file=sys.stderr, flush=True)
        print(bad_args, file=sys.stderr, flush=True)
    except ConversionException as cex:
        print(cex, file=sys.stderr, flush=True)
    except AbortedConversionException as acex:
        print(acex)
        exit(0)
    except Exception:
        print(traceback.format_exc(), file=sys.stderr, flush=True)

    exit(1)


def cli_entry():
    asyncio.run(main())


if __name__ == "__main__":
    cli_entry()
