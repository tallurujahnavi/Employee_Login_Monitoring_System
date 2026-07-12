from user_agents import parse


def get_device_details(user_agent_string):

    user_agent = parse(user_agent_string)

    browser = (
        f"{user_agent.browser.family} "
        f"{user_agent.browser.version_string}"
    )

    operating_system = (
        f"{user_agent.os.family} "
        f"{user_agent.os.version_string}"
    )

    device = user_agent.device.family

    return browser, operating_system, device