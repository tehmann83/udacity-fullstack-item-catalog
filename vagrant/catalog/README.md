# Item Catalog Project - Udacity Fullstack Nanodegree
---

## About

This project consists of developing an application that provides a list of items within a variety of categories, as well as provide a user registration and authentication system.

- CRUD support using Flask and SQLAlchemy
- API JSON Endpoints
- OAuth using Google Signin API

## How to run the program

1. Download and install [Vagrant](https://www.vagrantup.com/downloads.html).
2. Download and install [VirtualBox](https://www.virtualbox.org).
3. Clone the Vagrant VM config file from [Udacity](https://github.com/udacity/fullstack-nanodegree-vm).
4. Open the directory and navigate to `/vagrant`
5. Launch Vagrant
```bash
$ vagrant up
```
6. Start vagrant
```bash
$ vagrant ssh
```
6. Cd into /vagrant
7. Initialize database
```bash
$ python database_setup.py
```
8. Populate database with some initial data
```bash
$ python dummy_db.py
```
9. Launch application
```bash
$ python views.py
```
10. Open your browser and visit http://localhost:5000
