import sqlite3
import image
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from os.path import exists as pathexists
from imset import get_imset

config = {}
def use_config(_config):
  global config
  config = _config

def start(update, context):
  for key in ('make', 'guess'):
    if key in context.chat_data:
      del(context.chat_data[key])
  context.bot.send_message(
    chat_id=update.effective_chat.id,
    text="Hi! I'm Codenames training bot. " +
      "First, you need to setup a team. " + 
      "Players can only interact with the players from the same team. "+
      "Type `/team [team_name]` to start. " +
      "You can always type `/help` for the list of commands",
    reply_markup=config.keyboard.empty,
    parse_mode='Markdown')

def help(update, context):
  context.bot.send_message(
    chat_id=update.effective_chat.id,
    text="`/team [team_name]` sets up the team you are going to play in. " + 
      "Players can only interact with the players from the same team.\n"+
      "`/name [your_name]` sets up your name in the game.\n" +
      "`/make` allows you to create an association.\n" +
      "`/guess` allows you to guess others association.\n" +
      "`/stat` outputs statistics.\n" +
      "`/help` outputs this message",
    reply_markup=config.keyboard.action,
    parse_mode='Markdown')

def get_user_name(update):
  user_name = update.effective_user.first_name
  if update.effective_user.last_name:
    user_name += " " + update.effective_user.last_name
  return user_name

def team(update, context):
  teamname = " ".join(context.args)
  if teamname == "":
    teamname = "People who forget arguments"
  user_id = update.effective_user.id
  user_name = get_user_name(update)
  db = sqlite3.connect(config.db)
  query_pars = {
    "id": user_id,
    "name": user_name,
    "team": teamname,
    "chat_id": update.effective_chat.id
  }
  print(f"User {user_name} went to team {teamname}")
  with db:
    res = sum(1 for row in db.execute("select id from users where id=:id", query_pars))
    if res:
      db.execute("""update users
          set team=:team, chat_id=:chat_id
          where id=:id""", query_pars)
    else:
      db.execute("""insert into users(id, name, team, chat_id)
        values(:id, :name, :team, :chat_id)""", query_pars)
  db.close()
  context.bot.send_message(chat_id=update.effective_chat.id,
    text=f"Well done! You are in the team “{teamname}” now. "+
    "Input `/make` to create associations for your team or "+
    "`/guess` to guess associations from other people.",
    reply_markup=config.keyboard.action,
    parse_mode='Markdown')

def name(update, context):
  user_name = " ".join(context.args)
  user_id = update.effective_user.id
  # user_name = get_user_name(update)
  if user_name == "":
    user_name = f"Person{np.random.randint(1000)}"
  teamname = "Default team"
  db = sqlite3.connect(config.db)
  query_pars = {
    "id": user_id,
    "name": user_name,
    "team": teamname,
    "chat_id": update.effective_chat.id
  }
  print(f"User {user_name} changed the name")
  with db:
    res = sum(1 for row in db.execute("select id from users where id=:id", query_pars))
    if res:
      db.execute("""update users
          set name=:name where id=:id""", query_pars)
    else:
      db.execute("""insert into users(id, name, team, chat_id)
        values(:id, :name, :team, :chat_id)""", query_pars)
  db.close()
  context.bot.send_message(chat_id=update.effective_chat.id,
    text=f"Your name is {user_name} now.",
    reply_markup=config.keyboard.action,
    parse_mode='Markdown')

def make(update, context):
  imset = get_imset(" ".join(context.args))
  tile_ids, selected = image.random_tiling(imset.shape, imset.nos)
  fname = image.generate_image(tile_ids, imset.shape, selected)
  context.chat_data['make'] = {
    'img_code': image.repr_tile_ids_selected(tile_ids, selected)
  }
  context.bot.send_photo(
    chat_id=update.effective_chat.id,
    photo=open(fname, 'rb'),
    caption="Input one word associated with the green cards")

def make_answer(update, context):
  img_code = context.chat_data['make'].get('img_code')
  if not img_code:
    context.bot.send_message(chat_id=update.effective_chat.id,
      text=f"Something went wrong")
    return

  print(f"User {get_user_name(update)} created association {update.message.text}")
  db = sqlite3.connect(config.db)
  query_pars = {
    "user_id": update.effective_user.id,
    "img_code": img_code,
    "association": update.message.text
  }
  with db:
    db.execute("""
      insert into questions(user_id, img_code, association)
      values(:user_id, :img_code, :association)""", query_pars)
  db.close()
  context.chat_data['make'] = None
  context.bot.send_message(chat_id=update.effective_chat.id,
    text=f"I have remembered your association")

def propose_image_to_guess(user_id):
  db = sqlite3.connect(config.db)
  with db:
    row = None
    for row in db.execute("""
      select q.id, q.user_id, q.img_code, q.association, u.name from (
        select q.id, q.user_id, q.img_code, q.association
        from (select * from questions
          where user_id in (
            select u2.id from users as u1
            left join users as u2
            on u1.team = u2.team
            where u1.id = :user_id and u2.id!=:user_id
            )) as q
        left join guesses as g on q.id = g.question_id
        where g.id is NULL
        order by random()
        limit 1) as q
      left join users as u on q.user_id = u.id
    """, {'user_id': user_id}):
      break
  db.close()
  return row

def guess(update, context):
  quest = propose_image_to_guess(update.effective_user.id)
  if not quest:
    return context.bot.send_message(chat_id=update.effective_chat.id,
      text=f"Sorry, no images for you to guess", reply_markup=config.keyboard.action)
    
  qid, _, img_code, association, user_name = quest
  tile_ids, gt = image.from_repr(img_code)
  imset_name = f"{len(gt)}/{len(tile_ids)}"
  imset = get_imset(imset_name)
  if imset.shape[0]*imset.shape[1] != len(tile_ids):
    return context.bot.send_message(chat_id=update.effective_chat.id,
      text=f"Something went wrong", reply_markup=config.keyboard.action) 
  
  fname = image.guess_imagename(tile_ids)
  if not pathexists(fname):
    fname = image.generate_image(tile_ids, imset.shape)
  context.chat_data['guess'] = {
    'qid': qid,
    'tile_ids': img_code,
    'gt': gt,
    'guess': []
  }

  caption = f"{user_name} says “{association} {len(gt)}”"
  keyboard = config.keyboard.get(imset_name, config.keyboard.empty)
  context.bot.send_photo(
    chat_id=update.effective_chat.id,
    photo=open(fname, 'rb'),
    caption=caption,
    reply_markup=keyboard)

def save_guess(uid, qid, guess, res_tup):
  db = sqlite3.connect(config.db)
  with db:
    db.execute("""
      insert into guesses(user_id, question_id, guess, result, out_of)
      values(:uid, :qid, :guess, :result, :out_of)""", {
      'uid': uid,
      'qid': qid,
      'guess': image.repr_array(guess),
      'result': res_tup[0],
      'out_of': res_tup[1]
      })
  db.close()

def format_correct_tiles(tiles):
  strs = [str(t) for t in tiles]
  if len(tiles) > 1:
    if len(tiles) > 2:
      _and = ", and "
    else:
      _and = " and "
    strs[-1] = _and + strs[-1]
  return ", ".join(strs[:-1]) + strs[-1]

def guess_answer(update, context):
  guess = context.chat_data['guess']
  max_num = len(guess['tile_ids'])
  def incorrect_input():
    context.bot.send_message(chat_id=update.effective_chat.id,
      text=f"Input number from 1 to {max_num}")
  try:
    tile_num = int(update.message.text) - 1
  except ValueError:
    return incorrect_input()
  if tile_num < 0 or tile_num >= max_num:
    return incorrect_input()
  if tile_num in guess['guess']:
    return context.bot.send_message(chat_id=update.effective_chat.id,
      text=f"You have already guessed {tile_num+1}")

  end = False
  if tile_num in guess['gt']:
    guess['guess'].append(tile_num)
    message = "✅ That is correct{}"
    if len(guess['gt']) == len(guess['guess']):
      end = True
  else:
    message = "❌ That is wrong{}. "
    message += f"Correct tiles were {format_correct_tiles(1+guess['gt'])}"
    end = True

  if end:
    res_tup = (len(guess['guess']), len(guess['gt']))
    save_guess(update.effective_user.id,
      guess['qid'], guess['guess'], res_tup)
    message = message.format(". You scored {}/{}".format(*res_tup))
    reply_markup = config.keyboard.action
    print(f"User {get_user_name(update)} scored {res_tup[0]}")
  else:
    message = message.format("")
    reply_markup = None
  context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=message, reply_markup=reply_markup)

def stat(update, context):
  user_id = update.effective_user.id
  guessed = {}
  questioned = {}
  names = {}
  db = sqlite3.connect(config.db)
  with db:
    for row in db.execute("""
      select gid, qid, u1.name, u2.name, res, out from (
        select g.user_id as gid, q.user_id as qid, SUM(g.result) as res, SUM(g.out_of) as out
        from guesses as g
        left join questions as q on g.question_id = q.id
        where g.user_id = :user_id or q.user_id = :user_id
        group by g.user_id, q.user_id
      )
      left join users as u1 on gid == u1.id
      left join users as u2 on qid == u2.id
      """, {"user_id": user_id}):
      gid, qid, gname, qname, res, out = row
      if gid == user_id:
        guessed[qid] = (res, out)
        names[qid] = qname
      elif qid == user_id:
        questioned[gid] = (res, out)
        names[gid] = gname
  db.close()

  uids = sorted(list(set(guessed.keys()) | set(questioned.keys())))
  lines = []
  for uid in uids:
    if uid in guessed:
      tup = guessed[uid]
      tup = (names[uid],) + tup + (int(100*tup[0]/tup[1]),)
      lines.append("You understood {} {}/{} ({}%)".format(*tup))
    if uid in questioned:
      tup = questioned[uid]
      tup = (names[uid],) + tup + (int(100*tup[0]/tup[1]),)
      lines.append("{} understood you {}/{} ({}%)".format(*tup))

  context.bot.send_message(chat_id=update.effective_chat.id,
    text="\n".join(lines),
    reply_markup=config.keyboard.action,
    parse_mode='Markdown')

