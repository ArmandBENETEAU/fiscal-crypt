# **fiscal-crypt**

<p align="center">
  <img src="doc/images/fiscal_crypt.png" alt="Fiscal-crypt logo"/>
</p>

`fiscal-crypt` is an open source tool, allowing to help in the calculation of the tax declaration for your crypto-currencies trade.

## Installation

In order to work correctly with Coinbase Pro and Coinbase exchanges, `fiscalcrypt` needs the following python libraries:

* `cbpro`
* `coinbase`

To install them, simply run the following command lines in your terminal:

```bash
# Installation of coinbase-pro API
$ pip3 install cbpro

# Installation of coinbase API
$ pip3 install coinbase
```

Then, clone this repository locally and go in it:

```bash
$ git clone https://github.com/ArmandBENETEAU/fiscal-crypt.git
$ cd fiscal-crypt/
```

## Configuration

### API keys

In order to interact correctly with your exchange platform, `fiscalcrypt` needs your token in order to get your account activity and your transactions.
Please, follow the online documentation of your platform in order to create these tokens. `fiscalcrypt` only needs **read** privileges on your account! 
In general, please do not give to foreign tools rights that they should not have!

* Click [here](https://help.coinbase.com/en/exchange/managing-my-account/how-to-create-an-api-key) to learn about creating an api key on Coinbase
* Click [here](https://help.coinbase.com/en/pro/other-topics/api/how-do-i-create-an-api-key-for-coinbase-pro) to learn about creating an api key on Coinbase Pro

Coinbase will give you an api key and a secret, when Coinbase pro will give you a key, a secret and a passphrase. Copy every item somewhere because `fiscalcrypt` will need it.

`fiscalcrypt` also needs to evaluate the values of all your crypto-currencies, and to be really accurate I suggest to use Cryptowatch. So if you want to be really accurate and to not encounter problem during tax evaluation, I suggest to create a Cryptowatch account (it is completely free!) and to create a API key here as well.

* In Cryptowatch, on your account goes under "API Access" and click on "Generate key" to create your API key.

### Configuration file edition

### Basic explanations

In the repository, you can find the perfect example for you if you have a Coinbase and a Coinbase Pro account. 
In this case, copy the file and rename it to `fiscalcrypt_config.json`. Then change the keys fields with yours.

### Advanced explanations

If you want to learn more about how this configuration file work, here we go:

In the first part of the file, you can define the "price finders". They are the objects that will be able to get the price of any crypto-currency at a given datetime. Since Coinbase Pro utility seemed to be a bit clumsy about several currencies, I've added Cryptowatch that is looking more resilient.

In the second part of the file, you can define the "platforms". They are the platforms that you are using for trading. You give your API keys, secret and eventually passphrases. But you can specify also which price finders you want to use for each platform. It allows a flexibility on price finders to use per platform. Moreover, the order of the price finders is important since it will be used with this priority order!

## Use

Once you have correcly followed the previous paragraph, it is really simple to use!

Simply run the following command:

```bash
$ ./fiscalcrypt
```

You can also specified you configuration file (if its name is different than 'fiscalcrypt_config.json'):

```bash
$ ./fiscalcrypt /home/armand/my-config.json
```

`fiscalcrypt` will output the sell and buy operations it sees in the command line output, but it creates as well a `results.json` file at the end of the operations.
This `results.json` file is more complete and can be directly used to do the tax declaration (for French tax the number of the cases are specified).

## Limitation

For the moment, `fiscalcrypt` works only with the following exchange platforms:

* **Coinbase**
* **Coinbase Pro**

For the moment, `fiscalcrypt` works only with the following tax system:

* **French taxes system**

## Responsability

`fiscal-crypt` allows to **HELP** any crypto-currency owner to calculate his tax declaration.

The developer(s) do **NOT** guarantee that: 

* `fiscal-crypt` will be free from errors, bugs or default
* `fiscal-crypt` standard use will answer to any user specific use case

`fiscal-crypt` developer(s) cannot be considered as responsible for any error in the user's tax declaration.
Only the user is responsible to check that the tax declaration details given by `fiscal-crypt` are correct.

## Credits

The `fiscal-crypt` logo has been created using two logos made by [Freepik](https://fr.freepik.com/), from [Flaticon](www.flaticon.com)