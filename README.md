# Vantage QLink For HomeAssistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

A Home Assistant custom integration to interact with [Vantage's QLink System](https://dealer.vantagecontrols.com/downloads/Vantage%20QLink%20Program%20Examples%20Book%204th%20Edition.pdf) via an [IP Enabler](https://vantageemea.com/technical/IP%20Enabler.pdf)

While, the best solution for Vantage is to update to the InFusion system and use the [HASS Infusion integration](https://github.com/loopj/home-assistant-vantage) that's not possible for everyone.

## Features

* Integrate your vantage loads via their Contractor Number
* Level control (brightness)
* Polls the loads

## Future

* Blinds / Relays
* Find a way to subscribe to system changes instead of polling
* Automatic discovery

## Installation

The easiest way to install this integration is by using [HACS](https://hacs.xyz).

If you have HACS installed, you can add the Vantage integration by using this My button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bassrock&repository=hass-vantage-qlink&category=integration)

<details>
<summary>
<h4>Manual installation</h4>
</summary>

If you aren't using HACS, you can download the [latest release](https://github.com/bassrock/hass-vantage-qlink/releases/latest/download/hass-vantage-qlink.zip) and extract the contents to your Home Assistant `config/custom_components` directory.
</details>

## Configuration

1. Open a port on the IP Enabler
2. When setting up the integration you must provide a Comma Seperated List of contractor number ids of the laods you want to show in home assistant.

If you need to re-configure the loads in the system, click re-configure and then reload the integration after changing them
