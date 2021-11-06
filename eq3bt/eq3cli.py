""" Cli tool for testing connectivity with EQ3 smart thermostats. """
import sys
if sys.version_info < (3,4):
    print("To use this script you need python 3.4 or newer! got %s" % sys.version_info)
    sys.exit(1)

import logging
import click
import re
from click_datetime import Datetime

from eq3bt import Thermostat

pass_dev = click.make_pass_decorator(Thermostat)


def validate_mac(ctx, param, mac):
    if re.match('^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac) is None:
        raise click.BadParameter(mac + ' is no valid mac address')
    return mac

@click.group(invoke_without_command=True)
@click.option('--mac', envvar="EQ3_MAC", required=True, callback=validate_mac)
@click.option('--interface', default=None)
@click.option('--debug/--normal', default=False)
@click.pass_context
def cli(ctx, mac, interface, debug):
    """ Tool to query and modify the state of EQ3 BT smart thermostat. """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    thermostat = Thermostat(mac, interface)
    thermostat.update()
    ctx.obj = thermostat

    if ctx.invoked_subcommand is None:
        ctx.invoke(state)


@cli.command()
@click.option('--target', type=float, required=False)
@pass_dev
def temp(dev, target):
    """ Gets or sets the target temperature."""
    click.echo("Current target temp: %s" % dev.target_temperature)
    if target:
        click.echo("Setting target temp: %s" % target)
        dev.target_temperature = target


@cli.command()
@click.option('--target', type=int, required=False)
@pass_dev
def mode(dev, target):
    """ Gets or sets the active mode. """
    click.echo("Current mode: %s" % dev.mode_readable)
    if target:
        click.echo("Setting mode: %s" % target)
        dev.mode = target


@cli.command()
@click.option('--target', type=bool, required=False)
@pass_dev
def boost(dev, target):
    """ Gets or sets the boost mode. """
    click.echo("Boost: %s" % dev.boost)
    if target is not None:
        click.echo("Setting boost: %s" % target)
        dev.boost = target


@cli.command()
@pass_dev
def valve_state(dev):
    """ Gets the state of the valve. """
    click.echo("Valve: %s" % dev.valve_state)


@cli.command()
@click.option('--target', type=bool, required=False)
@pass_dev
def locked(dev, target):
    """ Gets or sets the lock. """
    click.echo("Locked: %s" % dev.locked)
    if target is not None:
        click.echo("Setting lock: %s" % target)
        dev.locked = target


@cli.command()
@pass_dev
def low_battery(dev):
    """ Gets the low battery status. """
    click.echo("Batter low: %s" % dev.low_battery)


@cli.command()
@click.option('--temp', type=float, required=False)
@click.option('--duration', type=float, required=False)
@pass_dev
def window_open(dev, temp, duration):
    """ Gets and sets the window open settings. """
    click.echo("Window open: %s" % dev.window_open)
    if dev.window_open_temperature is not None:
        click.echo("Window open temp: %s" % dev.window_open_temperature)
    if dev.window_open_time is not None:
        click.echo("Window open time: %s" % dev.window_open_time)
    if temp and duration:
        click.echo("Setting window open conf, temp: %s duration: %s" % (temp, duration))
        dev.window_open_config(temp, duration)


@cli.command()
@click.option('--comfort', type=float, required=False)
@click.option('--eco', type=float, required=False)
@pass_dev
def presets(dev, comfort, eco):
    """ Sets the preset temperatures for auto mode. """
    if dev.comfort_temperature is not None:
        click.echo("Current comfort temp: %s" % dev.comfort_temperature)
    if dev.eco_temperature is not None:
        click.echo("Current eco temp: %s" % dev.eco_temperature)
    if comfort and eco:
        click.echo("Setting presets: comfort %s, eco %s" % (comfort, eco))
        dev.temperature_presets(comfort, eco)


@cli.command()
@pass_dev
def schedule(dev):
    """ Gets the schedule from the thermostat. """
    # TODO: expose setting the schedule somehow?
    for d in range(7):
        dev.query_schedule(d)
    for day in dev.schedule.values():
        click.echo("Day %s, base temp: %s" % (day.day, day.base_temp))
        current_hour = day.next_change_at
        for hour in day.hours:
            if current_hour == 0: continue
            click.echo("\t[%s-%s] %s" % (current_hour, hour.next_change_at, hour.target_temp))
            current_hour = hour.next_change_at


@cli.command()
@click.argument('offset', type=float, required=False)
@pass_dev
def offset(dev, offset):
    """ Sets the temperature offset [-3,5 3,5] """
    if dev.temperature_offset is not None:
        click.echo("Current temp offset: %s" % dev.temperature_offset)
    if offset is not None:
        click.echo("Setting the offset to %s" % offset)
        dev.temperature_offset = offset


@cli.command()
@click.argument('away_end', type=Datetime(format='%Y-%m-%d %H:%M'), default=None, required=False)
@click.argument('temperature', type=float, default=None, required=False)
@pass_dev
def away(dev, away_end, temperature):
    """ Enables or disables the away mode. """
    if away_end:
        click.echo("Setting away until %s, temperature: %s" % (away_end, temperature))
    else:
        click.echo("Disabling away mode")
    dev.set_away(away_end, temperature)


@cli.command()
@pass_dev
def device(dev):
    """ Displays basic device information. """
    dev.query_id()
    click.echo("Firmware version: %s" % dev.firmware_version)
    click.echo("Device serial:    %s" % dev.device_serial)


@cli.command()
@click.pass_context
def state(ctx):
    """ Prints out all available information. """
    dev = ctx.obj
    click.echo(dev)
    ctx.forward(locked)
    ctx.forward(low_battery)
    ctx.forward(window_open)
    ctx.forward(boost)
    ctx.forward(temp)
    ctx.forward(presets)
    ctx.forward(offset)
    ctx.forward(mode)
    ctx.forward(valve_state)


if __name__ == "__main__":
    cli()
