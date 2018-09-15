require('json')

class Test
  class << self
    def init
      @@action_map ||= JSON.parse(File.read('action_map.json'))
    end

    def action(verb)
      puts @@action_map[verb]
    end
  end

  init
end

puts Test.action('like')