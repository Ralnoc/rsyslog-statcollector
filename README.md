# rsyslog-statcollector
Scrapes the rsyslog impstats output file and submits it to Graphite.

This was created to address the need to have a better visualization of 
the [rsyslog](https://github.com/rsyslog/rsyslog) impstats output. It scrapes 
the impstats file and processes the content into a series of graphite metrics 
which it them submits to [Graphite](https://github.com/graphite-project/graphite-web). 
I specifically chose graphite due to the fact that it is a very powerful metric 
visualizer, but when you pair it with [Grafana](https://github.com/grafana/grafana), 
you take the displaying of and interacting with your metrics to a whole new level.

It is important to remember that to get the most out of this script, you need
to not only have it scraping the impstats file, but you have to make use of the 
name="" options for all of your rulesets and actions. This is important so that 
you can make sure that the metrics are being properly separated out. Otherwise 
you could end up with metrics overwriting eachother.

## Example Rsyslog Configuration
As you can see below, every action and ruleset has a name="" option assigned 
to it. This is extremely important because rsyslog uses those names in the
impstats output. Rsyslog-statcollector in turn uses those labels in generating
the graphite metric tree. This allows you to have a nice and organized set of
metrics in graphite.

```
# Global Options
global(maxMessageSize="2048k")
global(preserveFQDN="on")

# Rsyslog plugins
module(load="impstats"
       interval="60"
       severity="7"
       log.file="/var/log/rsyslog-stats") # Provides Rsyslog Stats capability
module(load="imptcp" Threads="32")        # provides Plain TCP syslog reception
module(load="imudp" Threads="32")         # provides UDP syslog reception

# Local Log Processing Ruleset
ruleset(name="local.main_Q"){

# Log all kernel messages to the console.
# Logging much else clutters up the screen.
# kern.*                                                 action(name="local_kern"
#                                                               type="omfile"
#                                                               FileCreateMode="0644"
#                                                               DirCreateMode="0755"
#                                                               File="/dev/console")

# Log anything (except mail) of level info or higher.
# Don't log private authentication messages!
*.info;local1.none;mail.none;authpriv.none;cron.none;syslog.!=debug    action(name="local.messages"
                                                                              type="omfile"
                                                                              FileCreateMode="0600"
                                                                              DirCreateMode="0755"
                                                                              File="/log/local/messages")

# The authpriv file has restricted access.
authpriv.*                                              action(name="local.authpriv"
                                                               type="omfile"
                                                               FileCreateMode="0600"
                                                               DirCreateMode="0755"
                                                               File="/log/local/secure")

# Log all the mail messages in one place.
mail.*                                                  action(name="local.mail"
                                                               type="omfile"
                                                               FileCreateMode="0644"
                                                               DirCreateMode="0755"
                                                               File="/log/local/maillog")

# Log cron stuff
cron.*                                                  action(name="local.cron"
                                                               type="omfile"
                                                               FileCreateMode="0644"
                                                               DirCreateMode="0755"
                                                               File="/log/local/cron")

# Everybody gets emergency messages
*.emerg                                                 :omusrmsg:*

# Save news errors of level crit and higher in a special file.
uucp,news.crit                                          action(name="local.uucp_news"
                                                               type="omfile"
                                                               FileCreateMode="0644"
                                                               DirCreateMode="0755"
                                                               File="/log/local/spooler")

# Save boot messages also to boot.log
local7.*                                                action(name="local.bootlog"
                                                               type="omfile"
                                                               FileCreateMode="0644"
                                                               DirCreateMode="0755"
                                                               File="/log/local/boot.log")
}

```
